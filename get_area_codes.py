"""
Enrich the cleaned Christchurch Airbnb dataset with Stats NZ Statistical
Area 2 (SA2) area codes and names using the Koordinates Query API.

Input:
    - listings_data/listings_christchurch_cleaned.csv
      Cleaned Christchurch Airbnb listings containing latitude and longitude.

Main steps:
    1. Read the cleaned Airbnb dataset.
    2. Validate that latitude and longitude columns are available.
    3. Round coordinates and create unique coordinate keys.
    4. Test the Stats NZ SA2 layer and identify its code/name fields.
    5. Query Koordinates for each unique coordinate.
    6. Cache completed lookups so interrupted runs can resume.
    7. Join the returned SA2 area code and area name back to the listings.
    8. Check the percentage of listings successfully matched to an SA2 area.

Output:
    - listings_data/listings_christchurch_with_area.csv
      Airbnb data containing the added area_code and area_name columns.
    - listings_data/area_code_cache.csv
      Cached coordinate lookups used to avoid repeating API requests.

API key:
    The Koordinates API key is read from the KOORDINATES_KEY environment
    variable. The key is not stored directly in this source file.

Setup:
    macOS/Linux:
        export KOORDINATES_KEY="your_key_here"

    Windows CMD:
        set KOORDINATES_KEY=your_key_here

    Windows PowerShell:
        $env:KOORDINATES_KEY="your_key_here"

Usage:
    python get_area_codes.py --test    # test one coordinate and stop
    python get_area_codes.py           # process all remaining coordinates

The script is resumable because completed lookups are stored in the cache.
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

HOSTS = ["https://koordinates.com", "https://datafinder.stats.govt.nz"]
DEFAULT_LAYER = 123515
LAT_COL, LON_COL = "latitude", "longitude"
N_WORKERS = 8
CHECKPOINT_EVERY = 500

KEY = os.environ.get("KOORDINATES_KEY")
HOST = None
LAYER = DEFAULT_LAYER


def raw_query(host, lat, lon, radius):
    """Send one Koordinates query and return its features and status."""

    params = dict(
        key=KEY,
        layer=LAYER,
        x=lon,
        y=lat,
        max_results=1,
        radius=radius
    )

    note = "no response"

    for attempt in range(5):
        try:
            r = requests.get(
                f"{host}/services/query/v1/vector.json",
                params=params,
                timeout=30
            )

        except requests.RequestException as e:
            note = f"network error: {e.__class__.__name__}"
            time.sleep(2 ** attempt)
            continue

        if r.status_code == 200:
            try:
                return (
                    r.json()["vectorQuery"]["layers"][str(LAYER)]["features"],
                    "ok"
                )

            except (KeyError, ValueError):
                return (
                    None,
                    "unexpected response structure: " + r.text[:200]
                )

        note = f"HTTP {r.status_code}"

        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)
            continue

        return None, note

    return None, note


def find_fields(props):
    """Identify the SA2 code and area-name fields returned by Koordinates."""

    code = next(
        (
            k for k in props
            if "SA2" in k.upper()
            and "NAME" not in k.upper()
        ),
        None
    )

    name = next(
        (
            k for k in props
            if "SA2" in k.upper()
            and "NAME" in k.upper()
        ),
        None
    )

    return code, name


def lookup(lat, lon):
    """Look up the SA2 area code and name for one coordinate pair."""

    for radius in (1, 1000):
        feats, _ = raw_query(HOST, lat, lon, radius)

        if feats is None:
            return None

        if feats:
            props = feats[0]["properties"]
            code, name = find_fields(props)

            return dict(
                area_code=props.get(code),
                area_name=props.get(name)
            )

    return dict(
        area_code=None,
        area_name=None
    )


def pick_host(lat, lon):
    """Find a Koordinates host that returns data for the selected SA2 layer."""

    for host in HOSTS:
        for radius in (1, 1000):
            feats, note = raw_query(host, lat, lon, radius)

            print(
                f"  {host} (radius {radius} m): {note}, "
                f"{0 if not feats else len(feats)} feature(s)"
            )

            if feats:
                return host, feats[0]["properties"]

    return None, None


def main():
    """Run the SA2 enrichment process and save the enriched Airbnb dataset."""

    global HOST, LAYER

    ap = argparse.ArgumentParser()

    ap.add_argument(
        "--test",
        action="store_true",
        help="run a single query and stop"
    )

    ap.add_argument(
        "--in",
        dest="in_file",
        default="listings_data/listings_christchurch_cleaned.csv"
    )

    ap.add_argument(
        "--out",
        dest="out_file",
        default="listings_data/listings_christchurch_with_area.csv"
    )

    ap.add_argument(
        "--cache",
        default="listings_data/area_code_cache.csv"
    )

    ap.add_argument(
        "--layer",
        type=int,
        default=DEFAULT_LAYER
    )

    args = ap.parse_args()
    LAYER = args.layer

    if not KEY:
        sys.exit(
            "Set the KOORDINATES_KEY environment variable first "
            "(see top of file)."
        )

    df = pd.read_csv(args.in_file)

    # ========================================================
    # DELIVERABLE 6 CHANGE 5: Validate coordinate columns
    #
    # PREVIOUS CODE:
    #     df = pd.read_csv(args.in_file)
    #     df["lat_r"] = df[LAT_COL].round(6)
    #     df["lon_r"] = df[LON_COL].round(6)
    #
    # MODIFIED CODE:
    # We check for the required coordinate columns before trying
    # to use them or sending API requests.
    #
    # NOTES:
    # Previously, the code immediately tried to use latitude and
    # longitude after reading the file. If either column was missing,
    # the script would fail later. The new validation makes the
    # expected input clear and catches the problem before any API
    # processing begins.
    # ========================================================
    required_columns = {LAT_COL, LON_COL}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Airbnb data is missing required columns: {sorted(missing_columns)}"
        )

    df["lat_r"] = df[LAT_COL].round(6)
    df["lon_r"] = df[LON_COL].round(6)

    df["coord_key"] = (
        df["lat_r"].astype(str)
        + ","
        + df["lon_r"].astype(str)
    )

    coords = df[
        ["lat_r", "lon_r", "coord_key"]
    ].drop_duplicates("coord_key")

    print(
        f"Testing layer {LAYER} with the first listing's coordinates..."
    )

    first = coords.iloc[0]

    HOST, props = pick_host(
        first["lat_r"],
        first["lon_r"]
    )

    if HOST is None:
        sys.exit(
            "\nNo host returned a result. Check: "
            "(1) key is correct, "
            "(2) layer ID is right for that site, "
            "(3) lat/lon aren't swapped. "
            "Copy the URL from the layer's Services tab to compare."
        )

    code_f, name_f = find_fields(props)

    print(
        f"Using host: {HOST}\n"
        f"Properties returned: {props}"
    )

    print(
        f"Detected code field: {code_f!r}, "
        f"name field: {name_f!r}"
    )

    if code_f is None:
        sys.exit(
            "Couldn't find the SA2 code field in the properties above; "
            "tell me what the field is called and I'll fix find_fields()."
        )

    if args.test:
        return

    cols = ["coord_key", "area_code", "area_name"]

    if os.path.exists(args.cache):
        done = pd.read_csv(
            args.cache,
            dtype={"area_code": "string"}
        )

    else:
        done = pd.DataFrame(columns=cols)

    todo = coords[
        ~coords["coord_key"].isin(done["coord_key"])
    ]

    print(
        f"\n{len(coords)} unique points; "
        f"{len(todo)} still to query"
    )

    results, failed = [], 0

    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:

        futures = {
            pool.submit(
                lookup,
                r.lat_r,
                r.lon_r
            ): r.coord_key
            for r in todo.itertuples()
        }

        for i, fut in enumerate(
            as_completed(futures),
            1
        ):
            res = fut.result()

            if res is None:
                failed += 1

            else:
                res["coord_key"] = futures[fut]
                results.append(res)

            if i % CHECKPOINT_EVERY == 0:
                print(
                    f"  {i}/{len(todo)} done "
                    f"({failed} failed so far)"
                )

                pd.concat(
                    [
                        done,
                        pd.DataFrame(
                            results,
                            columns=cols
                        )
                    ]
                )[cols].to_csv(
                    args.cache,
                    index=False
                )

    lookup_df = pd.concat(
        [
            done,
            pd.DataFrame(
                results,
                columns=cols
            )
        ]
    )[cols]

    lookup_df.to_csv(
        args.cache,
        index=False
    )

    if failed:
        print(
            f"\n{failed} lookups failed (network/rate limit). "
            "Re-run the script to retry only those."
        )

    out = (
        df.merge(
            lookup_df,
            on="coord_key",
            how="left"
        )
        .drop(
            columns=[
                "lat_r",
                "lon_r",
                "coord_key"
            ]
        )
    )

    out["area_code"] = (
        pd.to_numeric(
            out["area_code"],
            errors="coerce"
        )
        .astype("Int64")
    )

    # ========================================================
    # DELIVERABLE 6 CHANGE 6: SA2 match-rate sanity check
    #
    # PREVIOUS CODE:
    #     print("\nListings without an area code:",
    #           int(out["area_code"].isna().sum()),
    #           f"of {len(out)}")
    #
    # MODIFIED CODE:
    # We still report missing area codes, but we now also calculate
    # the proportion of listings that were successfully matched.
    #
    # NOTES:
    # The previous code already gave us useful information about
    # unmatched listings. We improved this by calculating a match
    # percentage. This makes the result easier to interpret as a
    # sanity check because we can quickly see how much of the Airbnb
    # dataset was successfully enriched with SA2 information.
    # ========================================================
    matched = out["area_code"].notna().sum()
    total = len(out)
    match_rate = matched / total if total > 0 else 0

    print(
        f"\nSanity check: {matched}/{total} listings received "
        f"an SA2 area code ({match_rate:.1%})."
    )

    print(
        "\nListings without an area code:",
        int(out["area_code"].isna().sum()),
        f"of {len(out)}"
    )

    print(
        out
        .drop_duplicates("area_code")[
            ["area_code", "area_name"]
        ]
        .dropna()
        .sort_values("area_code")
        .to_string(index=False)
    )

    out.to_csv(
        args.out_file,
        index=False
    )

    print(
        "\nSaved",
        args.out_file
    )


if __name__ == "__main__":
    main()