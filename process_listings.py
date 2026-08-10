"""
Pipeline:
  1. Load one dataset to sanity-check structure.
  2. Filter to Christchurch only.
  3. Add a month/year column derived from the filename.
  4. Repeat for every monthly file in listings_data/, concatenate.
  5. Produce summary statistics for all columns + missing value counts.
  6. Save the concatenated dataset to a new CSV.

Expected input layout:
  listings_data/
    listings_Oct25.csv
    listings_Nov25.csv
    listings_Dec25.csv
    listings_Jan26.csv
    ...
    listings_Jun26.csv

Adjust CHRISTCHURCH_FILTER_COL / CHRISTCHURCH_FILTER_VALUE below to match
whatever your raw listings.csv actually uses to identify the city
(common Inside Airbnb columns: 'city', 'neighbourhood', 'neighbourhood_cleansed').
"""
 
import re
from pathlib import Path
 
import pandas as pd
 
# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_DIR = Path("listings_data")
OUTPUT_FILE = Path("listings_data/listings_christchurch_oct25_jun26.csv")
SUMMARY_FILE = Path("listings_data/listings_christchurch_summary.csv")
 
# Columns to try for identifying Christchurch, in priority order.
# Different Inside Airbnb export formats use different column names:
#   - "detailed" listings.csv (~97 cols): region_parent_name = "Christchurch City"
#   - "simplified" summary listings.csv (~18 cols): neighbourhood_group = "Christchurch City"
# Both are structured/exact values (not free text), so we match exactly rather
# than with .str.contains, to avoid accidentally matching things like
# "Christchurch Bay" or similar near-misses in other columns.
CHRISTCHURCH_FILTER_COL_CANDIDATES = [
    "region_parent_name",   # detailed export
    "neighbourhood_group",  # simplified export
    "region_name",
    "city",
    "neighbourhood_cleansed",
    "neighbourhood",        # free text typed by hosts — least reliable, used as last resort
]
CHRISTCHURCH_FILTER_VALUE = "Christchurch City"
 
# Map filename month names/abbreviations -> month_number
# Handles both styles found in this dataset (e.g. 'Dec25' and 'April26')
MONTH_MAP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}
 
 
def parse_month_year_from_filename(filename: str):
    """
    Extracts month/year from a filename like 'listings_Oct25.csv' -> (2025, 10, 'Oct-2025')
    or 'listings_April26.csv' -> (2026, 4, 'April-2026'). Handles both abbreviated
    and full month names.
    """
    match = re.search(r"([A-Za-z]+)(\d{2})", filename)
    if not match:
        raise ValueError(f"Could not parse month/year from filename: {filename}")
    month_str, year_str = match.groups()
    month_key = month_str.lower()
    if month_key not in MONTH_MAP:
        raise ValueError(f"Unrecognized month '{month_str}' in filename: {filename}")
    month_num = MONTH_MAP[month_key]
    year_num = 2000 + int(year_str)
    label = f"{month_str.capitalize()}-{year_num}"
    return year_num, month_num, label
 
 
def detect_filter_column(df: pd.DataFrame) -> str:
    """Finds which candidate column actually exists in this dataset."""
    for col in CHRISTCHURCH_FILTER_COL_CANDIDATES:
        if col in df.columns:
            return col
    raise ValueError(
        f"None of {CHRISTCHURCH_FILTER_COL_CANDIDATES} found in columns: {list(df.columns)}. "
        "Update CHRISTCHURCH_FILTER_COL_CANDIDATES to match your data."
    )
 
 
def load_and_filter(filepath: Path, verbose: bool = True) -> pd.DataFrame:
    """Step 1-3 for a single file: load, filter to Christchurch, tag with month/year."""
    df = pd.read_csv(filepath, low_memory=False)
    n_raw = len(df)
 
    filter_col = detect_filter_column(df)
 
    # 'neighbourhood' is free text typed by hosts, so use a loose contains-match.
    # Everything else (region_parent_name, neighbourhood_group, etc.) is a controlled
    # category value, so match it exactly to avoid near-miss false positives.
    if filter_col == "neighbourhood":
        mask = df[filter_col].astype(str).str.contains("Christchurch", case=False, na=False)
    else:
        mask = df[filter_col].astype(str).str.strip().str.lower() == CHRISTCHURCH_FILTER_VALUE.lower()
 
    n_match = mask.sum()
 
    if verbose:
        print(f"  filter column used: '{filter_col}' | raw rows: {n_raw} | matched: {n_match}")
        if n_match == 0:
            sample_vals = df[filter_col].dropna().unique()[:5]
            print(f"    -> 0 matches. Sample '{filter_col}' values in this file: {list(sample_vals)}")
 
    df = df[mask].copy()
 
    year, month, label = parse_month_year_from_filename(filepath.name)
    df["year"] = year
    df["month"] = month
    df["month_year"] = label
 
    return df
 
 
def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produces per-column summary stats:
      - numeric columns: min, max, mean, std, missing count
      - categorical columns: number of unique categories, top category + its count, missing count
    """
    rows = []
    for col in df.columns:
        s = df[col]
        missing = s.isna().sum()
 
        if pd.api.types.is_numeric_dtype(s):
            rows.append({
                "column": col,
                "dtype": "numeric",
                "min": s.min(),
                "max": s.max(),
                "mean": s.mean(),
                "std": s.std(),
                "n_unique_categories": None,
                "top_category": None,
                "top_category_count": None,
                "missing_count": missing,
                "missing_pct": round(100 * missing / len(df), 2),
            })
        else:
            vc = s.value_counts(dropna=True)
            top_cat = vc.index[0] if not vc.empty else None
            top_count = vc.iloc[0] if not vc.empty else None
            rows.append({
                "column": col,
                "dtype": "categorical",
                "min": None,
                "max": None,
                "mean": None,
                "std": None,
                "n_unique_categories": s.nunique(dropna=True),
                "top_category": top_cat,
                "top_category_count": top_count,
                "missing_count": missing,
                "missing_pct": round(100 * missing / len(df), 2),
            })
    return pd.DataFrame(rows)
 
 
def main():
    files = sorted(DATA_DIR.glob("listings_*.csv"))
    if not files:
        raise FileNotFoundError(f"No listings_*.csv files found in {DATA_DIR}/")
 
    print(f"Found {len(files)} files:")
    for f in files:
        print(f"  - {f.name}")
 
    # Step 1: load ONE dataset first, as a sanity check (also shows detected filter column)
    first_df = load_and_filter(files[0])
    print(f"\nLoaded + filtered '{files[0].name}': {len(first_df)} Christchurch rows")
    print(f"Columns detected: {list(first_df.columns)[:10]} ... ({len(first_df.columns)} total)")
 
    # Steps 3-4: repeat for every file, concatenate
    all_frames = [first_df]
    raw_col_counts = {files[0].name: len(pd.read_csv(files[0], nrows=0).columns)}
    for f in files[1:]:
        df = load_and_filter(f)
        print(f"Loaded + filtered '{f.name}': {len(df)} Christchurch rows")
        all_frames.append(df)
        raw_col_counts[f.name] = len(pd.read_csv(f, nrows=0).columns)
 
    # Schema consistency check: warn loudly if files don't all have the same
    # column count, since that usually means different export formats
    # (e.g. Inside Airbnb's "detailed" ~97-col file vs "simplified" ~18-col file)
    # got mixed together, which will badly distort missing-value stats downstream.
    distinct_counts = set(raw_col_counts.values())
    if len(distinct_counts) > 1:
        print("\n*** WARNING: files have inconsistent column counts — likely mixed export formats ***")
        for fname, ncols in raw_col_counts.items():
            print(f"    {fname}: {ncols} columns")
        print("    Concatenating anyway, but missing-value stats below will be misleading")
        print("    for any column that only exists in some files. Fix the source files first.\n")
 
    combined = pd.concat(all_frames, ignore_index=True)
    print(f"\nCombined dataset: {len(combined)} rows, {len(combined.columns)} columns")
    print(f"Months covered: {sorted(combined['month_year'].unique(), key=lambda x: (int(x.split('-')[1]), MONTH_MAP[x.split('-')[0].lower()]))}")
 
    # Step 5: summary statistics
    summary = build_summary(combined)
    summary.to_csv(SUMMARY_FILE, index=False)
    print(f"\nSummary statistics saved to: {SUMMARY_FILE}")
    print(summary.to_string(index=False))
 
    # Step 6: save concatenated dataset
    combined.to_csv(OUTPUT_FILE, index=False)
    print(f"\nConcatenated dataset saved to: {OUTPUT_FILE}")
 
 
if __name__ == "__main__":
    main()
