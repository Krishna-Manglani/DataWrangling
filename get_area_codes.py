"""
Add Stats NZ Statistical Area 2 (SA2) codes to the cleaned Christchurch
Airbnb dataset using the Koordinates Query API.

The script:
1. Loads the cleaned Airbnb dataset.
2. Creates unique coordinate keys from latitude and longitude.
3. Reuses previous API results stored in area_code_cache.csv.
4. Queries Koordinates only for coordinates that are not already cached.
5. Adds area_code and area_name back to all Airbnb rows.
6. Runs sanity checks and saves the enriched dataset.

This allows new Airbnb months to be processed without repeating API
requests for locations that have already been matched.

Input:
    listings_data/listings_christchurch_cleaned.csv

Outputs:
    listings_data/listings_christchurch_with_area.csv
    listings_data/area_code_cache.csv

API key:
    Set the KOORDINATES_KEY environment variable before running this script.

Usage:
    python get_area_codes.py
    python get_area_codes.py --test
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
import requests


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

HOSTS = [
    "https://koordinates.com",
    "https://datafinder.stats.govt.nz",
]

DEFAULT_LAYER = 123515

DEFAULT_INPUT = Path(
    "listings_data/listings_christchurch_cleaned.csv"
)

DEFAULT_OUTPUT = Path(
    "listings_data/listings_christchurch_with_area.csv"
)

DEFAULT_CACHE = Path(
    "listings_data/area_code_cache.csv"
)

LAT_COL = "latitude"
LON_COL = "longitude"

N_WORKERS = 8
CHECKPOINT_EVERY = 500
MAX_RETRIES = 5

HOST = None
LAYER = DEFAULT_LAYER


# ---------------------------------------------------------------------------
# Koordinates API functions
# ---------------------------------------------------------------------------

def raw_query(host, lat, lon, radius, api_key):
    """
    Send one request to the Koordinates Vector Query API.

    Temporary server and rate-limit errors are retried automatically.
    """
    params = {
        "key": api_key,
        "layer": LAYER,
        "x": lon,
        "y": lat,
        "max_results": 1,
        "radius": radius,
    }

    note = "no response"

    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                f"{host}/services/query/v1/vector.json",
                params=params,
                timeout=30,
            )

        except requests.RequestException as error:
            note = f"network error: {error.__class__.__name__}"
            time.sleep(2 ** attempt)
            continue

        if response.status_code == 200:
            try:
                features = (
                    response.json()
                    ["vectorQuery"]
                    ["layers"]
                    [str(LAYER)]
                    ["features"]
                )

                return features, "ok"

            except (KeyError, ValueError):
                return None, "unexpected API response"

        note = f"HTTP {response.status_code}"

        if response.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue

        return None, note

    return None, note


def find_fields(properties):
    """
    Find the SA2 code and SA2 name fields returned by the API.
    """
    code_field = next(
        (
            column
            for column in properties
            if "SA2" in column.upper()
            and "NAME" not in column.upper()
        ),
        None,
    )

    name_field = next(
        (
            column
            for column in properties
            if "SA2" in column.upper()
            and "NAME" in column.upper()
        ),
        None,
    )

    return code_field, name_field


def pick_host(lat, lon, api_key):
    """
    Test available Koordinates hosts and return the first working host.
    """
    for host in HOSTS:
        for radius in (1, 1000):
            features, note = raw_query(
                host,
                lat,
                lon,
                radius,
                api_key,
            )

            count = len(features) if features else 0

            print(
                f"  {host} (radius {radius} m): "
                f"{note}, {count} feature(s)"
            )

            if features:
                return host, features[0]["properties"]

    return None, None


def lookup(lat, lon, api_key):
    """
    Look up the SA2 area code and name for one coordinate.
    """
    for radius in (1, 1000):
        features, _ = raw_query(
            HOST,
            lat,
            lon,
            radius,
            api_key,
        )

        # None means the API request itself failed.
        if features is None:
            return None

        if features:
            properties = features[0]["properties"]

            code_field, name_field = find_fields(
                properties
            )

            if code_field is None:
                return None

            return {
                "area_code": properties.get(code_field),
                "area_name": properties.get(name_field),
            }

    # The request succeeded but the location had no spatial match.
    return {
        "area_code": None,
        "area_name": None,
    }


# ---------------------------------------------------------------------------
# Airbnb input preparation
# ---------------------------------------------------------------------------

def load_listings(filepath):
    """
    Load the cleaned Airbnb dataset and validate its coordinates.
    """
    filepath = Path(filepath)

    if not filepath.exists():
        raise FileNotFoundError(
            f"Input file not found: {filepath}"
        )

    df = pd.read_csv(
        filepath,
        low_memory=False,
    )

    if df.empty:
        raise ValueError(
            "Airbnb input dataset is empty."
        )

    required = {
        LAT_COL,
        LON_COL,
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required column(s): {sorted(missing)}"
        )

    if df[[LAT_COL, LON_COL]].isna().any().any():
        raise ValueError(
            "Missing latitude or longitude values found."
        )

    if not df[LAT_COL].between(-90, 90).all():
        raise ValueError(
            "Invalid latitude values found."
        )

    if not df[LON_COL].between(-180, 180).all():
        raise ValueError(
            "Invalid longitude values found."
        )

    return df


def prepare_coordinates(df):
    """
    Create rounded coordinate keys and a table of unique locations.
    """
    prepared = df.copy()

    prepared["lat_r"] = (
        prepared[LAT_COL]
        .round(6)
    )

    prepared["lon_r"] = (
        prepared[LON_COL]
        .round(6)
    )

    prepared["coord_key"] = (
        prepared["lat_r"].astype(str)
        + ","
        + prepared["lon_r"].astype(str)
    )

    coords = (
        prepared[
            [
                "lat_r",
                "lon_r",
                "coord_key",
            ]
        ]
        .drop_duplicates("coord_key")
        .reset_index(drop=True)
    )

    if coords.empty:
        raise ValueError(
            "No coordinates available for SA2 lookup."
        )

    return prepared, coords


# ---------------------------------------------------------------------------
# Cache functions
# ---------------------------------------------------------------------------

def load_cache(filepath):
    """
    Load previous coordinate lookups.

    If no cache exists, return an empty cache.
    """
    filepath = Path(filepath)

    columns = [
        "coord_key",
        "area_code",
        "area_name",
    ]

    if not filepath.exists():
        return pd.DataFrame(
            columns=columns
        )

    cache = pd.read_csv(
        filepath,
        dtype={
            "coord_key": "string",
            "area_code": "string",
            "area_name": "string",
        },
    )

    missing = set(columns) - set(cache.columns)

    if missing:
        raise ValueError(
            f"Cache is missing column(s): {sorted(missing)}"
        )

    cache = (
        cache[columns]
        .drop_duplicates(
            "coord_key",
            keep="last",
        )
        .reset_index(drop=True)
    )

    return cache


def save_cache(cache, filepath):
    """
    Save coordinate lookup results to the cache.
    """
    filepath = Path(filepath)

    filepath.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    cache.to_csv(
        filepath,
        index=False,
    )


def get_uncached_coordinates(coords, cache):
    """
    Return coordinates that have not already been processed.
    """
    if cache.empty:
        return coords.copy()

    cached_keys = set(
        cache["coord_key"]
        .dropna()
        .astype(str)
    )

    todo = coords[
        ~coords["coord_key"]
        .astype(str)
        .isin(cached_keys)
    ].copy()

    return todo


# ---------------------------------------------------------------------------
# Query new coordinates
# ---------------------------------------------------------------------------

def query_new_coordinates(
    todo,
    cache,
    cache_file,
    api_key,
):
    """
    Query uncached coordinates in parallel and update the cache.

    Progress is checkpointed so completed API requests are not lost if the
    process is interrupted.
    """
    new_results = []
    failed = 0

    with ThreadPoolExecutor(
        max_workers=N_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                lookup,
                row.lat_r,
                row.lon_r,
                api_key,
            ): row.coord_key

            for row in todo.itertuples()
        }

        for number, future in enumerate(
            as_completed(futures),
            start=1,
        ):
            coord_key = futures[future]

            try:
                result = future.result()

            except Exception:
                result = None

            if result is None:
                failed += 1

            else:
                result["coord_key"] = coord_key
                new_results.append(result)

            # Save progress regularly.
            if (
                number % CHECKPOINT_EVERY == 0
                or number == len(todo)
            ):
                checkpoint = pd.concat(
                    [
                        cache,
                        pd.DataFrame(new_results),
                    ],
                    ignore_index=True,
                )

                checkpoint = (
                    checkpoint
                    .drop_duplicates(
                        "coord_key",
                        keep="last",
                    )
                )

                save_cache(
                    checkpoint,
                    cache_file,
                )

                print(
                    f"  {number}/{len(todo)} processed "
                    f"({failed} failed)"
                )

    updated_cache = pd.concat(
        [
            cache,
            pd.DataFrame(new_results),
        ],
        ignore_index=True,
    )

    updated_cache = (
        updated_cache
        .drop_duplicates(
            "coord_key",
            keep="last",
        )
        .reset_index(drop=True)
    )

    save_cache(
        updated_cache,
        cache_file,
    )

    return updated_cache, failed


# ---------------------------------------------------------------------------
# Join SA2 results back to Airbnb
# ---------------------------------------------------------------------------

def add_area_codes(df, cache):
    """
    Join cached SA2 information back to all Airbnb rows.
    """
    original_rows = len(df)

    output = df.merge(
        cache[
            [
                "coord_key",
                "area_code",
                "area_name",
            ]
        ],
        on="coord_key",
        how="left",
        validate="many_to_one",
    )

    if len(output) != original_rows:
        raise ValueError(
            "Row count changed after joining area codes."
        )

    output = output.drop(
        columns=[
            "lat_r",
            "lon_r",
            "coord_key",
        ]
    )

    output["area_code"] = (
        pd.to_numeric(
            output["area_code"],
            errors="coerce",
        )
        .astype("Int64")
    )

    return output


def sanity_check(original, output):
    """
    Run final validation and report the SA2 match rate.
    """
    if output.empty:
        raise ValueError(
            "Final output dataset is empty."
        )

    if len(output) != len(original):
        raise ValueError(
            "Final output row count does not match input."
        )

    required = {
        LAT_COL,
        LON_COL,
        "area_code",
        "area_name",
    }

    missing = required - set(output.columns)

    if missing:
        raise ValueError(
            f"Final output is missing: {sorted(missing)}"
        )

    matched = int(
        output["area_code"]
        .notna()
        .sum()
    )

    total = len(output)

    match_rate = (
        matched / total
        if total
        else 0
    )

    print(
        f"\nSanity check: "
        f"{matched}/{total} listings received "
        f"an SA2 area code ({match_rate:.1%})."
    )

    print(
        "Listings without an area code:",
        int(
            output["area_code"]
            .isna()
            .sum()
        ),
        f"of {total}",
    )


# ---------------------------------------------------------------------------
# Command-line arguments
# ---------------------------------------------------------------------------

def parse_args():
    """
    Read command-line options.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Add Stats NZ SA2 area codes "
            "to Christchurch Airbnb listings."
        )
    )

    parser.add_argument(
        "--test",
        action="store_true",
        help="test the API with one uncached coordinate and stop",
    )

    parser.add_argument(
        "--in",
        dest="in_file",
        default=str(DEFAULT_INPUT),
        help="input cleaned Airbnb CSV",
    )

    parser.add_argument(
        "--out",
        dest="out_file",
        default=str(DEFAULT_OUTPUT),
        help="output Airbnb CSV with SA2 areas",
    )

    parser.add_argument(
        "--cache",
        default=str(DEFAULT_CACHE),
        help="coordinate lookup cache",
    )

    parser.add_argument(
        "--layer",
        type=int,
        default=DEFAULT_LAYER,
        help="Koordinates layer ID",
    )

    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main pipeline stage
# ---------------------------------------------------------------------------

def main():
    """
    Run the complete SA2 enrichment stage.
    """
    global HOST, LAYER

    args = parse_args()
    LAYER = args.layer

    # Load and validate the latest cleaned Airbnb dataset.
    df = load_listings(
        args.in_file
    )

    print(
        f"Loaded Airbnb dataset: "
        f"{len(df)} rows, "
        f"{len(df.columns)} columns"
    )

    print(
        "Input coordinate sanity checks passed."
    )

    # Prepare unique locations.
    prepared, coords = prepare_coordinates(
        df
    )

    print(
        f"Unique coordinates: {len(coords)}"
    )

    # Reuse previous geocoding work.
    cache = load_cache(
        args.cache
    )

    todo = get_uncached_coordinates(
        coords,
        cache,
    )

    print(
        f"Coordinates already cached: {len(cache)}"
    )

    print(
        f"New coordinates requiring lookup: {len(todo)}"
    )

    # Contact Koordinates only when new coordinates need processing.
    if not todo.empty:
        api_key = os.environ.get(
            "KOORDINATES_KEY"
        )

        if not api_key:
            sys.exit(
                "New coordinates require Koordinates, but "
                "KOORDINATES_KEY is not set."
            )

        first = todo.iloc[0]

        print(
            f"\nTesting layer {LAYER} "
            "with the first new coordinate..."
        )

        HOST, properties = pick_host(
            first["lat_r"],
            first["lon_r"],
            api_key,
        )

        if HOST is None:
            sys.exit(
                "\nNo Koordinates host returned a result. "
                "The existing cache has not been changed. "
                "Check the API service and try again."
            )

        code_field, name_field = find_fields(
            properties
        )

        if code_field is None:
            sys.exit(
                "Could not identify the SA2 code field "
                "returned by the API."
            )

        print(
            f"Using host: {HOST}"
        )

        print(
            f"Detected fields: "
            f"{code_field}, {name_field}"
        )

        if args.test:
            print(
                "API test successful. "
                "No dataset changes were made."
            )
            return

        print(
            f"\nQuerying {len(todo)} "
            "new coordinates..."
        )

        cache, failed = query_new_coordinates(
            todo,
            cache,
            args.cache,
            api_key,
        )

        if failed:
            print(
                f"Warning: {failed} coordinate lookup(s) failed. "
                "They will be retried on the next run."
            )

    else:
        print(
            "All coordinates are already cached. "
            "No API requests are needed."
        )

        if args.test:
            print(
                "Test complete: "
                "no uncached coordinates to query."
            )
            return

    # Add SA2 information to every listing-month row.
    output = add_area_codes(
        prepared,
        cache,
    )

    sanity_check(
        df,
        output,
    )

    # Save the updated geocoded Airbnb dataset.
    output_path = Path(
        args.out_file
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.to_csv(
        output_path,
        index=False,
    )

    print(
        "\nFinal sanity checks passed."
    )

    print(
        f"Saved enriched dataset to: "
        f"{output_path}"
    )

    print(
        f"Coordinate cache: "
        f"{args.cache}"
    )


if __name__ == "__main__":
    main()