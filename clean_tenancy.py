"""
Deliverable 4: Clean the Tenancy Services rental bond dataset.

Pipeline:
  1. Load the Detailed Quarterly Rental Bond dataset.
  2. Check that all expected columns are present.
  3. Retain all useful columns.
  4. Convert TimeFrame from DD/MM/YYYY to a proper date.
  5. Filter the timeframe to match the Airbnb dataset.
  6. Standardise selected text fields.
  7. Check for exact duplicate records.
  8. Check and document missing values.
  9. Validate bond count and rent fields.
 10. Check the logical ordering of rent quartiles.
 11. Run final sanity checks.
 12. Save the cleaned dataset and cleaning log.

Airbnb comparison period:
  October 2025 to June 2026

Matching Tenancy quarters:
  1 October 2025
  1 January 2026
  1 April 2026

Expected input:
  tenancy_data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv

Outputs:
  tenancy_data/tenancy_cleaned.csv
  tenancy_data/tenancy_cleaning_log.csv
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# These variables define where the original Tenancy dataset is located
# and where our cleaned dataset and cleaning log will be saved.
#
# Keeping the file paths together makes the script easier to maintain.
# We also save the cleaned data separately instead of overwriting the
# original downloaded dataset.

DATA_FILE = Path(
    "tenancy_data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
)

OUTPUT_FILE = Path(
    "tenancy_data/tenancy_cleaned.csv"
)

CLEANING_LOG_FILE = Path(
    "tenancy_data/tenancy_cleaning_log.csv"
)


# ---------------------------------------------------------------------------
# Columns
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# We reviewed all 12 columns in the Tenancy dataset.
#
# Unlike the Airbnb dataset, we did not find any column that was
# completely empty or clearly redundant.
#
# Therefore, all 12 columns were retained.
#
# Location Id and TimeFrame are especially important because the
# Deliverable 4 instructions specifically require us to keep them.

COLUMNS_TO_KEEP = [
    "TimeFrame",
    "Location Id",
    "Dwelling Type",
    "Number Of Beds",
    "Total Bonds",
    "Active Bonds",
    "Closed Bonds",
    "Median Rent",
    "Geometric Mean Rent",
    "Upper Quartile Rent",
    "Lower Quartile Rent",
    "Log Std Dev Weekly Rent",
]

COLUMNS_TO_DROP = []


# ---------------------------------------------------------------------------
# Matching timeframe
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# Our Airbnb dataset covers October 2025 to June 2026.
#
# Airbnb is monthly, but the Tenancy dataset is quarterly.
#
# Therefore, we selected:
#
# Q4 2025 = October to December 2025
# Q1 2026 = January to March 2026
# Q2 2026 = April to June 2026
#
# Together these three quarters cover the same overall timeframe
# as the Airbnb dataset.

TIMEFRAMES_TO_KEEP = [
    pd.Timestamp("2025-10-01"),
    pd.Timestamp("2026-01-01"),
    pd.Timestamp("2026-04-01"),
]


# ---------------------------------------------------------------------------
# Cleaning log
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# Instead of only producing a cleaned dataset, we also record our
# cleaning decisions.
#
# The log records:
#   - what we did,
#   - why we did it,
#   - and what effect it had.
#
# This makes the cleaning process easier to explain and reproduce.

def add_log(
    log_rows: list,
    step: str,
    decision: str,
    reason: str,
    impact: str,
) -> None:
    """
    Add one cleaning decision to the cleaning log.

    The cleaning log records what was done, why it was done,
    and what consequence the decision had on the dataset.
    """
    log_rows.append(
        {
            "step": step,
            "decision": decision,
            "reason": reason,
            "impact": impact,
        }
    )


# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# We load the original downloaded Tenancy CSV directly into pandas.
#
# We do not manually edit the raw CSV. This means another team member
# can rerun the script and reproduce the same cleaning process.

def load_data(filepath: Path) -> pd.DataFrame:
    """
    Load the raw Detailed Quarterly Rental Bond dataset.

    The original downloaded dataset is read without modifying it.
    The script stops if the expected file cannot be found.
    """
    if not filepath.exists():
        raise FileNotFoundError(
            f"Could not find {filepath}. "
            "Check that the Tenancy dataset is inside tenancy_data."
        )

    return pd.read_csv(
        filepath,
        low_memory=False,
    )


# ---------------------------------------------------------------------------
# Check expected columns
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# Before cleaning, we check that the dataset still contains the
# 12 columns that our pipeline expects.
#
# This is a safety check. If the source dataset changes in the future,
# the script will stop instead of silently cleaning the wrong structure.

def check_expected_columns(df: pd.DataFrame) -> None:
    """
    Check that all expected Tenancy dataset columns are present.

    This prevents the pipeline from continuing if the source dataset
    has an unexpected structure.
    """
    missing_columns = [
        col
        for col in COLUMNS_TO_KEEP
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "The following expected columns are missing: "
            f"{missing_columns}"
        )


# ---------------------------------------------------------------------------
# Select columns
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# All 12 columns are retained.
#
# We do not remove a column simply because it contains some missing
# values. A column is removed only when there is a justified reason.
#
# In this dataset, every column still contains potentially useful
# information about location, property type, bonds, or rent.

def select_columns(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Retain all 12 original columns.

    No columns are removed because each column contains information
    that may be useful for the rental analysis.

    Location Id and TimeFrame are specifically retained because
    Deliverable 4 requires them for later analysis.
    """
    cleaned = df[
        COLUMNS_TO_KEEP
    ].copy()

    add_log(
        log_rows,
        step="Select columns",
        decision="Retained all 12 original columns",
        reason=(
            "All columns contain potentially useful rental bond "
            "information. Location Id and TimeFrame are also "
            "specifically required for later analysis."
        ),
        impact="0 columns removed",
    )

    return cleaned


# ---------------------------------------------------------------------------
# Filter timeframe
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# This is an important part of the cleaning process.
#
# The original Tenancy CSV stores TimeFrame as DD/MM/YYYY.
#
# For example:
#   1/10/2025 = 1 October 2025
#   1/01/2026 = 1 January 2026
#   1/04/2026 = 1 April 2026
#
# We explicitly tell pandas that the format is day/month/year.
# This prevents the day and month from being interpreted incorrectly.
#
# After converting the dates, we retain only the three quarters
# covering October 2025 through June 2026.
#
# This reduces the dataset from 226,080 rows to 27,212 rows.

def filter_timeframe(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Convert TimeFrame to a proper date and filter the dataset to the
    quarters covering October 2025 through June 2026.

    The raw Tenancy CSV stores TimeFrame using DD/MM/YYYY.

    Examples:
      1/10/2025 = 1 October 2025
      1/01/2026 = 1 January 2026
      1/04/2026 = 1 April 2026

    The format is explicitly specified as %d/%m/%Y so that pandas
    does not incorrectly interpret the day and month.
    """
    cleaned = df.copy()

    rows_before = len(cleaned)

    # PRESENTATION:
    # Convert the original text dates into proper datetime values.
    #
    # %d = day
    # %m = month
    # %Y = four-digit year
    cleaned["TimeFrame"] = pd.to_datetime(
        cleaned["TimeFrame"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    # Check whether any dates failed to convert.
    invalid_dates = (
        cleaned["TimeFrame"]
        .isna()
        .sum()
    )

    # PRESENTATION:
    # Keep only Q4 2025, Q1 2026, and Q2 2026.
    # These three quarters match the overall Airbnb timeframe.
    cleaned = cleaned[
        cleaned["TimeFrame"].isin(
            TIMEFRAMES_TO_KEEP
        )
    ].copy()

    rows_after = len(cleaned)

    add_log(
        log_rows,
        step="Filter timeframe",
        decision=(
            "Retained the three quarters covering "
            "October 2025 through June 2026"
        ),
        reason=(
            "This matches the overall timeframe of the "
            "Christchurch Airbnb dataset."
        ),
        impact=(
            f"{rows_before} rows -> {rows_after} rows; "
            f"{invalid_dates} invalid TimeFrame value(s)"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# Standardise text fields
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# We remove unnecessary spaces from categorical text fields.
#
# This helps make categories consistent. For example, "House" and
# "House " should not accidentally be treated as two different values.
#
# Number Of Beds stays as text because it contains categories such
# as ALL and 5+, not just ordinary numbers.

def standardise_text(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Standardise selected categorical text fields.

    Leading and trailing spaces are removed from Dwelling Type
    and Number Of Beds.

    Number Of Beds remains a text field because categories such as
    ALL and 5+ should not be forced into numeric values.
    """
    cleaned = df.copy()

    text_columns = [
        "Dwelling Type",
        "Number Of Beds",
    ]

    for col in text_columns:
        cleaned[col] = (
            cleaned[col]
            .astype("string")
            .str.strip()
        )

    add_log(
        log_rows,
        step="Standardise text fields",
        decision=(
            "Removed leading and trailing spaces from "
            "Dwelling Type and Number Of Beds"
        ),
        reason=(
            "Consistent categorical values reduce formatting "
            "inconsistencies without changing their meaning."
        ),
        impact="0 rows removed",
    )

    return cleaned


# ---------------------------------------------------------------------------
# Check duplicates
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# We check for completely identical rows.
#
# We do NOT treat repeated Location Id values as duplicates because
# the same location can legitimately have several records for
# different dwelling types or bedroom categories.
#
# Therefore, only exact duplicate rows are removed.

def check_duplicates(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Check for completely identical duplicate records.

    Only exact duplicate rows are removed.

    Repeated Location Id or TimeFrame values are not automatically
    duplicates because one location and quarter can contain several
    dwelling types and bedroom categories.
    """
    cleaned = df.copy()

    duplicate_count = (
        cleaned
        .duplicated()
        .sum()
    )

    if duplicate_count > 0:
        cleaned = (
            cleaned
            .drop_duplicates()
            .copy()
        )

    add_log(
        log_rows,
        step="Check exact duplicates",
        decision="Removed exact duplicate rows if present",
        reason=(
            "Completely identical rows provide no additional "
            "information, while repeated locations can legitimately "
            "occur for different property categories."
        ),
        impact=f"{duplicate_count} row(s) removed",
    )

    return cleaned


# ---------------------------------------------------------------------------
# Check missing values
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# We identify and document missing values instead of automatically
# deleting every incomplete row.
#
# A record can still contain useful information even when one field
# is missing.
#
# Some published Tenancy values may also be unavailable or suppressed.
#
# Our final dataset still contains:
#   Number Of Beds             = 890 missing
#   Location Id                = 94 missing
#   Median Rent                = 94 missing
#   Geometric Mean Rent        = 94 missing
#   Upper Quartile Rent        = 94 missing
#   Lower Quartile Rent        = 94 missing
#   Log Std Dev Weekly Rent    = 94 missing

def check_missing_values(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Check and document missing values without automatically deleting them.

    Missing values are retained because incomplete records may still
    contain useful information. Some published values may also be
    unavailable because of privacy suppression.

    Automatically deleting all incomplete rows could cause unnecessary
    data loss.
    """
    missing = (
        df
        .isna()
        .sum()
    )

    missing = (
        missing[
            missing > 0
        ]
        .sort_values(
            ascending=False
        )
    )

    if missing.empty:
        impact = "No missing values found"

    else:
        impact = "; ".join(
            f"{col}: {count}"
            for col, count in missing.items()
        )

    add_log(
        log_rows,
        step="Check missing values",
        decision="Retained legitimate missing values",
        reason=(
            "Missing values were not automatically removed because "
            "some may represent valid records with unavailable or "
            "suppressed information."
        ),
        impact=impact,
    )


# ---------------------------------------------------------------------------
# Validate numeric fields
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# We check important numeric variables using simple logical rules.
#
# Bond counts should never be negative.
#
# Available weekly rent values should be greater than zero.
#
# We check these values instead of automatically changing unusual
# observations because unusual does not always mean incorrect.

def validate_numeric_fields(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Validate important numeric variables.

    Bond counts are checked for negative values.

    Rent measures are checked for zero or negative values when present.

    Unusual values are checked rather than automatically removed because
    they should first be investigated in their data context.
    """
    bond_columns = [
        "Total Bonds",
        "Active Bonds",
        "Closed Bonds",
    ]

    rent_columns = [
        "Median Rent",
        "Geometric Mean Rent",
        "Upper Quartile Rent",
        "Lower Quartile Rent",
    ]

    invalid_bonds = {}

    for col in bond_columns:
        invalid_bonds[col] = (
            df[col].notna()
            &
            (df[col] < 0)
        ).sum()

    invalid_rents = {}

    for col in rent_columns:
        invalid_rents[col] = (
            df[col].notna()
            &
            (df[col] <= 0)
        ).sum()

    bond_impact = ", ".join(
        f"{col}={count}"
        for col, count in invalid_bonds.items()
    )

    rent_impact = ", ".join(
        f"{col}={count}"
        for col, count in invalid_rents.items()
    )

    add_log(
        log_rows,
        step="Validate numeric fields",
        decision=(
            "Checked bond counts and weekly rent measures "
            "for impossible values"
        ),
        reason=(
            "Bond counts should not be negative and observed "
            "weekly rent values should be greater than zero."
        ),
        impact=(
            f"Invalid bond counts: {bond_impact}; "
            f"invalid rent values: {rent_impact}"
        ),
    )


# ---------------------------------------------------------------------------
# Check rent ordering
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# This is a logical sanity check.
#
# When all three rent statistics are available, they should follow:
#
# Lower Quartile Rent <= Median Rent <= Upper Quartile Rent
#
# If this ordering is violated, the record should be investigated
# because the statistics would not make logical sense.

def check_rent_ordering(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Check the logical ordering of lower quartile, median,
    and upper quartile rent.

    When all three values are available, the expected order is:

        Lower Quartile Rent <= Median Rent <= Upper Quartile Rent

    Inconsistent records are identified for investigation rather than
    automatically deleted.
    """
    complete_rent_rows = df[
        [
            "Lower Quartile Rent",
            "Median Rent",
            "Upper Quartile Rent",
        ]
    ].notna().all(axis=1)

    invalid_order = (
        complete_rent_rows
        &
        (
            (
                df["Lower Quartile Rent"]
                >
                df["Median Rent"]
            )
            |
            (
                df["Median Rent"]
                >
                df["Upper Quartile Rent"]
            )
        )
    )

    invalid_count = (
        invalid_order
        .sum()
    )

    add_log(
        log_rows,
        step="Check rent ordering",
        decision=(
            "Checked Lower Quartile <= Median <= Upper Quartile"
        ),
        reason=(
            "The quartile and median values should follow a "
            "logical ordering when all three values are available."
        ),
        impact=(
            f"{invalid_count} record(s) require investigation"
        ),
    )


# ---------------------------------------------------------------------------
# Final sanity checks
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# Before saving the dataset, we perform final quality-control checks.
#
# We confirm:
#   - Location Id still exists.
#   - TimeFrame still exists.
#   - only the intended three quarters remain.
#   - all 12 intended columns remain.
#   - no exact duplicates remain.
#
# This prevents us from saving a dataset that does not match our
# intended cleaning rules.

def run_sanity_checks(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Run final checks on the cleaned Tenancy dataset.

    These checks confirm that:
      - Location Id is retained.
      - TimeFrame is retained.
      - only the three required quarterly periods remain.
      - all 12 intended columns remain.
      - no exact duplicate rows remain.
    """
    assert "Location Id" in df.columns
    assert "TimeFrame" in df.columns

    unexpected_timeframes = (
        ~df["TimeFrame"].isin(
            TIMEFRAMES_TO_KEEP
        )
    ).sum()

    remaining_duplicates = (
        df
        .duplicated()
        .sum()
    )

    assert unexpected_timeframes == 0, (
        "Unexpected TimeFrame values remain after filtering."
    )

    assert len(df.columns) == len(COLUMNS_TO_KEEP), (
        "Unexpected number of columns in cleaned dataset."
    )

    assert remaining_duplicates == 0, (
        "Exact duplicate rows remain after cleaning."
    )

    add_log(
        log_rows,
        step="Final sanity checks",
        decision=(
            "Confirmed required columns, timeframe, "
            "column count, and duplicates"
        ),
        reason=(
            "Final checks confirm that the cleaned dataset "
            "matches the intended structure."
        ),
        impact=(
            f"{len(df)} final rows; "
            f"{len(df.columns)} final columns; "
            f"{remaining_duplicates} exact duplicate(s) remain"
        ),
    )


# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# We save two outputs:
#
# 1. tenancy_cleaned.csv
#    This is the final cleaned dataset.
#
# 2. tenancy_cleaning_log.csv
#    This documents our cleaning decisions.
#
# We do not overwrite the original downloaded dataset.
#
# TimeFrame is saved in standard YYYY-MM-DD format to make it easier
# to work with in later analysis.

def save_outputs(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Save the cleaned Tenancy dataset and cleaning log.

    The raw downloaded dataset is not overwritten.

    TimeFrame is saved in standard YYYY-MM-DD format so that it can
    be used consistently in later analysis.
    """
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df = df.copy()

    output_df["TimeFrame"] = (
        output_df["TimeFrame"]
        .dt.strftime("%Y-%m-%d")
    )

    output_df.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    cleaning_log = pd.DataFrame(
        log_rows
    )

    cleaning_log.to_csv(
        CLEANING_LOG_FILE,
        index=False,
    )


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
# PRESENTATION GUIDE:
# This section gives us the easiest way to explain the entire pipeline.
#
# The workflow is:
#
# Load
#   ↓
# Check columns
#   ↓
# Keep useful columns
#   ↓
# Convert + filter timeframe
#   ↓
# Standardise text
#   ↓
# Check duplicates
#   ↓
# Check missing values
#   ↓
# Validate numeric fields
#   ↓
# Check rent ordering
#   ↓
# Final sanity checks
#   ↓
# Save cleaned dataset + cleaning log

def main():
    """
    Run the complete Deliverable 4 Tenancy Services cleaning pipeline.
    """
    log_rows = []

    # -----------------------------------------------------------------------
    # Step 1: Load raw dataset
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "We start with the original Tenancy Services dataset, which contains
    # 226,080 rows and 12 columns."

    df = load_data(
        DATA_FILE
    )

    original_rows = len(df)
    original_columns = len(df.columns)

    print(
        f"Loaded dataset: "
        f"{original_rows} rows, "
        f"{original_columns} columns"
    )

    # -----------------------------------------------------------------------
    # Step 2: Check structure
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "Before cleaning, we check that all 12 expected columns are present."

    check_expected_columns(
        df
    )

    # -----------------------------------------------------------------------
    # Step 3: Select columns
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "We reviewed all 12 columns and retained all of them because none
    # were completely empty or clearly redundant."

    cleaned = select_columns(
        df,
        log_rows,
    )

    print(
        f"Columns kept: {len(COLUMNS_TO_KEEP)}"
    )

    print(
        f"Columns dropped: {COLUMNS_TO_DROP}"
    )

    # -----------------------------------------------------------------------
    # Step 4: Convert and filter TimeFrame
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "The source stores dates as day/month/year, so we explicitly convert
    # them before filtering. We then retain the three quarters covering
    # October 2025 through June 2026."

    cleaned = filter_timeframe(
        cleaned,
        log_rows,
    )

    print(
        f"Rows after timeframe filter: "
        f"{len(cleaned)}"
    )

    print("TimeFrames retained:")

    print(
        cleaned["TimeFrame"]
        .value_counts()
        .sort_index()
    )

    # -----------------------------------------------------------------------
    # Step 5: Standardise text
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "We remove unnecessary spaces from categorical fields so values
    # are represented consistently."

    cleaned = standardise_text(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 6: Check duplicates
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "We check for exact duplicate rows. Repeated locations are allowed
    # because one location can contain different property categories."

    cleaned = check_duplicates(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 7: Check missing values
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "We document missing values rather than automatically deleting
    # incomplete observations, because they can still contain useful data."

    check_missing_values(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 8: Validate numeric fields
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "We check that bond counts are not negative and available rent
    # values are greater than zero."

    validate_numeric_fields(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 9: Check rent ordering
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "We check that lower quartile rent is less than or equal to the
    # median, and the median is less than or equal to the upper quartile."

    check_rent_ordering(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 10: Final sanity checks
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "Before saving, we confirm the required columns, correct timeframe,
    # expected column count, and absence of exact duplicates."

    run_sanity_checks(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 11: Save outputs
    # -----------------------------------------------------------------------
    # PRESENTATION:
    # "Finally, we save the cleaned dataset separately from the raw file
    # and create a cleaning log documenting our decisions."

    save_outputs(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Final results
    # -----------------------------------------------------------------------

    print("\nCleaning complete.")

    print(
        f"Original dataset: "
        f"{original_rows} rows, "
        f"{original_columns} columns"
    )

    print(
        f"Cleaned dataset: "
        f"{len(cleaned)} rows, "
        f"{len(cleaned.columns)} columns"
    )

    print(
        f"\nSaved cleaned dataset to: "
        f"{OUTPUT_FILE}"
    )

    print(
        f"Saved cleaning log to: "
        f"{CLEANING_LOG_FILE}"
    )

    print("\nMissing values remaining:")

    missing = (
        cleaned
        .isna()
        .sum()
    )

    print(
        missing[
            missing > 0
        ].sort_values(
            ascending=False
        )
    )

    print("\nMedian Rent summary:")

    print(
        cleaned["Median Rent"]
        .describe()
    )


if __name__ == "__main__":
    main()