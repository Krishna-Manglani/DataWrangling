"""
Add Stats NZ SA2 area codes to the cleaned Christchurch Airbnb data using the
Koordinates Query API.

Setup (never put your key in the code or commit it to GitHub):
    macOS/Linux:  export KOORDINATES_KEY="your_key_here"
    Windows CMD:  set KOORDINATES_KEY=your_key_here
    PowerShell:   $env:KOORDINATES_KEY="your_key_here"

Usage:
    python get_area_codes.py --test    # ONE query, prints the raw response
    python get_area_codes.py           # all unique coordinates (resumable)

Re-running is safe: finished lookups are cached in area_code_cache.csv and
failed ones are simply retried.
"""
import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd
import requests

# Hosts are tried in this order; the first one that accepts your key is used.
HOSTS = ["https://koordinates.com", "https://datafinder.stats.govt.nz"]
DEFAULT_LAYER = 123515          # Statistical Area 2 2026 (Stats NZ)
LAT_COL, LON_COL = "latitude", "longitude"
N_WORKERS = 8                   # the API is rate-limited, so stay polite
CHECKPOINT_EVERY = 500

KEY = os.environ.get("KOORDINATES_KEY")
HOST = None    # set in main() once a working host is found
LAYER = DEFAULT_LAYER


def raw_query(host, lat, lon, radius):
    """Return (features, note). features is None if the request failed."""
    params = dict(key=KEY, layer=LAYER, x=lon, y=lat, max_results=1, radius=radius)
    note = "no response"
    for attempt in range(5):
        try:
            r = requests.get(f"{host}/services/query/v1/vector.json",
                             params=params, timeout=30)
        except requests.RequestException as e:
            note = f"network error: {e.__class__.__name__}"
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 200:
            try:
                return r.json()["vectorQuery"]["layers"][str(LAYER)]["features"], "ok"
            except (KeyError, ValueError):
                return None, "unexpected response structure: " + r.text[:200]
        note = f"HTTP {r.status_code}"
        if r.status_code in (429, 500, 502, 503, 504):
            time.sleep(2 ** attempt)          # back off and retry
            continue
        return None, note                     # 401/403/404 etc.: don't retry
    return None, note


def find_fields(props):
    """Pick out the SA2 code and name properties."""
    code = next((k for k in props if "SA2" in k.upper() and "NAME" not in k.upper()), None)
    name = next((k for k in props if "SA2" in k.upper() and "NAME" in k.upper()), None)
    return code, name


def lookup(lat, lon):
    """One point -> dict, or None if the request failed (so it gets retried)."""
    for radius in (1, 1000):   # 1 m is enough inside a polygon; widen for coast
        feats, _ = raw_query(HOST, lat, lon, radius)
        if feats is None:
            return None
        if feats:
            props = feats[0]["properties"]
            code, name = find_fields(props)
            return dict(area_code=props.get(code), area_name=props.get(name))
    return dict(area_code=None, area_name=None)   # genuinely outside all areas


def pick_host(lat, lon):
    for host in HOSTS:
        for radius in (1, 1000):
            feats, note = raw_query(host, lat, lon, radius)
            print(f"  {host} (radius {radius} m): {note}, "
                  f"{0 if not feats else len(feats)} feature(s)")
            if feats:
                return host, feats[0]["properties"]
    return None, None


def main():
    global HOST, LAYER
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="run a single query and stop")
    ap.add_argument("--in", dest="in_file", default="listings_data/listings_christchurch_cleaned.csv")
    ap.add_argument("--out", dest="out_file", default="listings_data/listings_christchurch_with_area.csv")
    ap.add_argument("--cache", default="listings_data/area_code_cache.csv")
    ap.add_argument("--layer", type=int, default=DEFAULT_LAYER)
    args = ap.parse_args()
    LAYER = args.layer

    if not KEY:
        sys.exit("Set the KOORDINATES_KEY environment variable first (see top of file).")

    df = pd.read_csv(args.in_file)
    df["lat_r"] = df[LAT_COL].round(6)
    df["lon_r"] = df[LON_COL].round(6)
    df["coord_key"] = df["lat_r"].astype(str) + "," + df["lon_r"].astype(str)
    coords = df[["lat_r", "lon_r", "coord_key"]].drop_duplicates("coord_key")

    print(f"Testing layer {LAYER} with the first listing's coordinates...")
    first = coords.iloc[0]
    HOST, props = pick_host(first["lat_r"], first["lon_r"])
    if HOST is None:
        sys.exit("\nNo host returned a result. Check: (1) key is correct, (2) layer ID "
                 "is right for that site, (3) lat/lon aren't swapped. Copy the URL from "
                 "the layer's Services tab to compare.")
    code_f, name_f = find_fields(props)
    print(f"Using host: {HOST}\nProperties returned: {props}")
    print(f"Detected code field: {code_f!r}, name field: {name_f!r}")
    if code_f is None:
        sys.exit("Couldn't find the SA2 code field in the properties above; "
                 "tell me what the field is called and I'll fix find_fields().")
    if args.test:
        return

    # Resume from cache if a previous run was interrupted
    cols = ["coord_key", "area_code", "area_name"]
    if os.path.exists(args.cache):
        done = pd.read_csv(args.cache, dtype={"area_code": "string"})
    else:
        done = pd.DataFrame(columns=cols)
    todo = coords[~coords["coord_key"].isin(done["coord_key"])]
    print(f"\n{len(coords)} unique points; {len(todo)} still to query")

    results, failed = [], 0
    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
        futures = {pool.submit(lookup, r.lat_r, r.lon_r): r.coord_key
                   for r in todo.itertuples()}
        for i, fut in enumerate(as_completed(futures), 1):
            res = fut.result()
            if res is None:
                failed += 1
            else:
                res["coord_key"] = futures[fut]
                results.append(res)
            if i % CHECKPOINT_EVERY == 0:
                print(f"  {i}/{len(todo)} done ({failed} failed so far)")
                pd.concat([done, pd.DataFrame(results, columns=cols)])[cols] \
                    .to_csv(args.cache, index=False)

    lookup_df = pd.concat([done, pd.DataFrame(results, columns=cols)])[cols]
    lookup_df.to_csv(args.cache, index=False)
    if failed:
        print(f"\n{failed} lookups failed (network/rate limit). "
              "Re-run the script to retry only those.")

    out = df.merge(lookup_df, on="coord_key", how="left") \
            .drop(columns=["lat_r", "lon_r", "coord_key"])
    out["area_code"] = pd.to_numeric(out["area_code"], errors="coerce").astype("Int64")
    print("\nListings without an area code:", int(out["area_code"].isna().sum()),
          f"of {len(out)}")
    print(out.drop_duplicates("area_code")[["area_code", "area_name"]]
             .dropna().sort_values("area_code").to_string(index=False))
    out.to_csv(args.out_file, index=False)
    print("\nSaved", args.out_file)


if __name__ == "__main__":
    main()
