"""
Deliverable 4: Clean the Tenancy Services rental bond dataset.

Pipeline:
  1. Load the Detailed Quarterly Rental Bond dataset.
  2. Check that all expected columns are present.
  3. Convert TimeFrame to a date.
  4. Filter the dataset to match the Airbnb timeframe.
  5. Standardise selected text fields.
  6. Check for duplicate records.
  7. Check and document missing values.
  8. Validate bond count and rent fields.
  9. Check the ordering of rent quartiles.
 10. Run final sanity checks.
 11. Save the cleaned dataset and cleaning log.

Airbnb comparison period:
  October 2025 to June 2026

Matching Tenancy quarters:
  2025-10-01
  2026-01-01
  2026-04-01

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
# Columns to keep and drop
# ---------------------------------------------------------------------------

# All 12 original columns are retained.
# Location Id and TimeFrame are specifically required by Deliverable 4.

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

# No columns are considered unnecessary at this stage.

COLUMNS_TO_DROP = []


# ---------------------------------------------------------------------------
# Matching timeframe
# ---------------------------------------------------------------------------

# Airbnb data covers October 2025 through June 2026.
# These are the three quarterly TimeFrame values covering the same period.

TIMEFRAMES_TO_KEEP = [
    pd.Timestamp("2025-10-01"),
    pd.Timestamp("2026-01-01"),
    pd.Timestamp("2026-04-01"),
]


# ---------------------------------------------------------------------------
# Cleaning log
# ---------------------------------------------------------------------------

def add_log(
    log_rows: list,
    step: str,
    decision: str,
    reason: str,
    impact: str,
) -> None:
    """
    Add one cleaning decision to the cleaning log.

    Each entry records the cleaning step, decision, reason,
    and consequence so the cleaning process can be documented
    and reproduced.
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

def check_expected_columns(df: pd.DataFrame) -> None:
    """
    Check that all 12 expected Tenancy dataset columns are present.

    This prevents the cleaning pipeline from continuing if the
    downloaded dataset has a different structure.
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

def filter_timeframe(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Filter the quarterly Tenancy data to the same overall period
    covered by the Airbnb dataset.

    The Airbnb data covers October 2025 through June 2026.

    The matching quarterly TimeFrame values are:
      - 2025-10-01
      - 2026-01-01
      - 2026-04-01

    These represent Q4 2025, Q1 2026, and Q2 2026.
    """
    cleaned = df.copy()

    # Convert TimeFrame into a proper date.
    cleaned["TimeFrame"] = pd.to_datetime(
        cleaned["TimeFrame"],
        errors="coerce",
    )

    invalid_dates = (
        cleaned["TimeFrame"]
        .isna()
        .sum()
    )

    rows_before = len(cleaned)

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
            "Kept quarterly periods from October 2025 "
            "through June 2026"
        ),
        reason=(
            "This matches the overall timeframe of the "
            "Christchurch Airbnb dataset."
        ),
        impact=(
            f"{rows_before} rows -> {rows_after} rows; "
            f"{invalid_dates} invalid TimeFrame value(s) found"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# Standardise text fields
# ---------------------------------------------------------------------------

def standardise_text(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Standardise selected categorical text fields.

    Leading and trailing spaces are removed from Dwelling Type
    and Number Of Beds.

    Number Of Beds remains a text field because the dataset contains
    categories such as ALL and 5+, which should not be forced into
    numeric values.
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

def check_duplicates(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Check for completely identical duplicate records.

    Only exact duplicate rows are removed.

    Location Id and TimeFrame alone are not treated as a unique key
    because one location and quarter can legitimately contain several
    records for different dwelling types and bedroom categories.
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

def check_missing_values(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Check and document missing values without automatically deleting them.

    Missing rent values may be related to the privacy suppression used
    by Tenancy Services. Therefore, missing observations are retained
    unless there is clear evidence that a record is invalid.

    This avoids unnecessary data loss.
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
            "some may result from privacy suppression or represent "
            "valid records with unavailable information."
        ),
        impact=impact,
    )


# ---------------------------------------------------------------------------
# Validate numeric fields
# ---------------------------------------------------------------------------

def validate_numeric_fields(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Validate important numeric variables.

    Bond counts are checked for negative values.

    Rent measures are checked for zero or negative values when present.

    Values are checked rather than automatically modified because an
    unusual value should first be investigated in its data context.
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

def check_rent_ordering(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Check the logical ordering of lower quartile, median,
    and upper quartile rent.

    For records where all three values are available, the expected
    ordering is:

        Lower Quartile Rent <= Median Rent <= Upper Quartile Rent

    Records are identified for investigation rather than automatically
    deleted.
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

def run_sanity_checks(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Run final checks on the cleaned Tenancy dataset.

    These checks confirm that:
      - Location Id is retained.
      - TimeFrame is retained.
      - only the three matching quarterly periods remain.
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

def save_outputs(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Save the cleaned Tenancy dataset and cleaning log.

    The raw downloaded dataset is not overwritten.

    The cleaning log records the decisions, reasons, and consequences
    of the cleaning process.
    """
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df = df.copy()

    # Store TimeFrame consistently as YYYY-MM-DD.
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

def main():
    """
    Run the complete Deliverable 4 Tenancy Services cleaning pipeline.
    """
    log_rows = []

    # Step 1: Load raw dataset.

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

    # Step 2: Confirm expected structure.

    check_expected_columns(
        df
    )

    # Step 3: Keep all useful columns.

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

    # Step 4: Filter to the matching Airbnb timeframe.

    cleaned = filter_timeframe(
        cleaned,
        log_rows,
    )

    print(
        f"Rows after timeframe filter: "
        f"{len(cleaned)}"
    )

    print(
        "TimeFrames retained:"
    )

    print(
        cleaned["TimeFrame"]
        .value_counts()
        .sort_index()
    )

    # Step 5: Standardise text.

    cleaned = standardise_text(
        cleaned,
        log_rows,
    )

    # Step 6: Check duplicates.

    cleaned = check_duplicates(
        cleaned,
        log_rows,
    )

    # Step 7: Check missing values.

    check_missing_values(
        cleaned,
        log_rows,
    )

    # Step 8: Validate numeric values.

    validate_numeric_fields(
        cleaned,
        log_rows,
    )

    # Step 9: Check rent ordering.

    check_rent_ordering(
        cleaned,
        log_rows,
    )

    # Step 10: Final sanity checks.

    run_sanity_checks(
        cleaned,
        log_rows,
    )

    # Step 11: Save outputs.

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