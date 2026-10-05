"""
Clean and validate the Tenancy Services rental bond dataset.

This script prepares the Tenancy Services data used in the project's
Airbnb-versus-long-term-rental analysis.

The cleaning decisions are based on the work completed in the previous
deliverables. The script is structured so that it can also be run as one
stage of an automated pipeline.

Main steps:
    1. Load the raw Tenancy Services dataset.
    2. Check that the expected columns are present.
    3. Keep the 12 columns required for the project.
    4. Convert TimeFrame to a proper date.
    5. Filter to the tenancy quarters used in the project.
    6. Standardise selected text fields.
    7. Remove exact duplicate rows.
    8. Document missing values.
    9. Validate bond-count and rent fields.
   10. Check the logical ordering of rent statistics.
   11. Run final sanity checks.
   12. Save the cleaned dataset and cleaning log.

Input:
    tenancy_data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv

Outputs:
    tenancy_data/tenancy_cleaned.csv
    tenancy_data/tenancy_cleaning_log.csv

Run from the repository root:
    python clean_tenancy.py
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path("tenancy_data")

DATA_FILE = (
    DATA_DIR
    / "Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv"
)

OUTPUT_FILE = (
    DATA_DIR
    / "tenancy_cleaned.csv"
)

CLEANING_LOG_FILE = (
    DATA_DIR
    / "tenancy_cleaning_log.csv"
)


# These are the 12 columns retained from the original Tenancy dataset.
# Location Id is needed for geographic matching and TimeFrame is needed
# for matching quarterly periods.
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


# These are the quarterly periods established in the previous deliverable.
# They correspond to the tenancy comparison period used in the project.
TIMEFRAMES_TO_KEEP = [
    pd.Timestamp("2025-10-01"),
    pd.Timestamp("2026-01-01"),
    pd.Timestamp("2026-04-01"),
]


TEXT_COLUMNS = [
    "Dwelling Type",
    "Number Of Beds",
]


BOND_COLUMNS = [
    "Total Bonds",
    "Active Bonds",
    "Closed Bonds",
]


RENT_COLUMNS = [
    "Median Rent",
    "Geometric Mean Rent",
    "Upper Quartile Rent",
    "Lower Quartile Rent",
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

    Args:
        log_rows:
            List containing cleaning-log entries.
        step:
            Name of the cleaning step.
        decision:
            Cleaning action or decision.
        reason:
            Reason for the decision.
        impact:
            Observed effect on the dataset.
    """
    log_rows.append({
        "step": step,
        "decision": decision,
        "reason": reason,
        "impact": impact,
    })


# ---------------------------------------------------------------------------
# Load input
# ---------------------------------------------------------------------------

def load_data(filepath: Path) -> pd.DataFrame:
    """
    Load the raw Tenancy Services dataset.

    Args:
        filepath:
            Path to the raw Tenancy CSV.

    Returns:
        Loaded Tenancy DataFrame.

    Raises:
        FileNotFoundError:
            If the expected source file does not exist.
        ValueError:
            If the source dataset contains no rows.
    """
    if not filepath.exists():
        raise FileNotFoundError(
            f"Tenancy source file not found: {filepath}"
        )

    df = pd.read_csv(
        filepath,
        low_memory=False,
    )

    if df.empty:
        raise ValueError(
            f"Tenancy source dataset is empty: {filepath}"
        )

    return df


# ---------------------------------------------------------------------------
# Validate input structure
# ---------------------------------------------------------------------------

def check_expected_columns(df: pd.DataFrame) -> None:
    """
    Check that all columns required by the cleaning process are present.

    This is a fail-fast check for automation. If the source-data structure
    changes, the pipeline stops instead of silently producing an incomplete
    output.

    Args:
        df:
            Raw Tenancy DataFrame.

    Raises:
        ValueError:
            If one or more required columns are missing.
    """
    missing_columns = [
        column
        for column in COLUMNS_TO_KEEP
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Required Tenancy column(s) missing: "
            f"{missing_columns}"
        )


# ---------------------------------------------------------------------------
# Select project columns
# ---------------------------------------------------------------------------

def select_columns(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Retain the 12 Tenancy columns required by the project.

    No required columns are removed. Location Id and TimeFrame are retained
    because later analysis uses them to match geographic areas and periods.

    Args:
        df:
            Raw Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Returns:
        DataFrame containing the required columns.
    """
    cleaned = df[
        COLUMNS_TO_KEEP
    ].copy()

    add_log(
        log_rows,
        step="Select columns",
        decision="Retained all 12 required Tenancy columns",
        reason=(
            "All selected columns contain useful rental information. "
            "Location Id and TimeFrame are required for later analysis."
        ),
        impact=(
            f"{len(df.columns)} input columns -> "
            f"{len(cleaned.columns)} retained columns"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# TimeFrame cleaning and filtering
# ---------------------------------------------------------------------------

def clean_and_filter_timeframe(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Convert TimeFrame to datetime and retain the project comparison quarters.

    The raw TimeFrame values use DD/MM/YYYY. The format is specified
    explicitly to avoid ambiguity between day and month.

    Args:
        df:
            Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Returns:
        Tenancy data restricted to the required quarters.

    Raises:
        ValueError:
            If dates cannot be parsed, an expected quarter is missing, or
            filtering leaves no rows.
    """
    cleaned = df.copy()

    rows_before = len(
        cleaned
    )

    # Keep the original values temporarily so invalid dates can be detected.
    original_timeframe = cleaned[
        "TimeFrame"
    ].copy()

    cleaned["TimeFrame"] = pd.to_datetime(
        cleaned["TimeFrame"],
        format="%d/%m/%Y",
        errors="coerce",
    )

    invalid_dates = int(
        (
            original_timeframe.notna()
            & cleaned["TimeFrame"].isna()
        ).sum()
    )

    if invalid_dates > 0:
        raise ValueError(
            f"{invalid_dates} TimeFrame value(s) could not be parsed."
        )

    # Check that every expected project quarter exists in the source data
    # before filtering.
    available_timeframes = set(
        cleaned["TimeFrame"]
        .dropna()
        .tolist()
    )

    missing_timeframes = [
        timeframe
        for timeframe in TIMEFRAMES_TO_KEEP
        if timeframe not in available_timeframes
    ]

    if missing_timeframes:
        missing_labels = [
            timeframe.strftime("%Y-%m-%d")
            for timeframe in missing_timeframes
        ]

        raise ValueError(
            "Expected Tenancy quarter(s) missing from source data: "
            + ", ".join(missing_labels)
        )

    cleaned = cleaned[
        cleaned["TimeFrame"].isin(
            TIMEFRAMES_TO_KEEP
        )
    ].copy()

    if cleaned.empty:
        raise ValueError(
            "No Tenancy rows remain after timeframe filtering."
        )

    rows_after = len(
        cleaned
    )

    add_log(
        log_rows,
        step="Filter timeframe",
        decision=(
            "Retained the project Tenancy quarters: "
            + ", ".join(
                timeframe.strftime("%Y-%m-%d")
                for timeframe in TIMEFRAMES_TO_KEEP
            )
        ),
        reason=(
            "These are the quarterly Tenancy periods established "
            "for the project's rental comparison."
        ),
        impact=(
            f"{rows_before} rows -> {rows_after} rows"
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

    Leading and trailing whitespace is removed. Number Of Beds remains a
    text field because it can contain categories rather than only numbers.

    Args:
        df:
            Filtered Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Returns:
        DataFrame with standardised text values.
    """
    cleaned = df.copy()

    for column in TEXT_COLUMNS:
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .str.strip()
        )

    add_log(
        log_rows,
        step="Standardise text",
        decision=(
            "Trimmed Dwelling Type and Number Of Beds"
        ),
        reason=(
            "Removing unnecessary surrounding whitespace makes "
            "categorical values more consistent."
        ),
        impact="0 rows removed",
    )

    return cleaned


# ---------------------------------------------------------------------------
# Duplicate handling
# ---------------------------------------------------------------------------

def remove_exact_duplicates(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Remove completely identical duplicate rows.

    Repeated Location Id values are not treated as duplicates because a
    location can legitimately have multiple dwelling types, bedroom
    categories, and quarterly records.

    Args:
        df:
            Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Returns:
        DataFrame with exact duplicates removed.
    """
    cleaned = df.copy()

    duplicate_count = int(
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
        decision="Removed completely identical rows",
        reason=(
            "Exact duplicate rows add no new information, while "
            "repeated locations may legitimately represent different "
            "rental categories."
        ),
        impact=(
            f"{duplicate_count} row(s) removed"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# Missing-value documentation
# ---------------------------------------------------------------------------

def document_missing_values(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Document missing values without automatically deleting or imputing them.

    Missing values are retained because incomplete Tenancy records can still
    contain useful information and some published values may be unavailable.

    Args:
        df:
            Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.
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
            f"{column}: {int(count)}"
            for column, count in missing.items()
        )

    add_log(
        log_rows,
        step="Check missing values",
        decision="Retained legitimate missing values",
        reason=(
            "Automatically deleting or imputing all missing values "
            "could remove useful records or introduce unsupported data."
        ),
        impact=impact,
    )


# ---------------------------------------------------------------------------
# Numeric validation
# ---------------------------------------------------------------------------

def validate_numeric_fields(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Validate important numeric fields.

    Checks:
        - bond counts must not be negative;
        - available weekly rent values must be greater than zero.

    Missing values are not treated as invalid because the project has
    intentionally retained legitimate missing values.

    Args:
        df:
            Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Raises:
        ValueError:
            If impossible numeric values are detected.
    """
    invalid_bonds = {}

    for column in BOND_COLUMNS:
        invalid_bonds[column] = int(
            (
                df[column].notna()
                & (df[column] < 0)
            ).sum()
        )

    invalid_rents = {}

    for column in RENT_COLUMNS:
        invalid_rents[column] = int(
            (
                df[column].notna()
                & (df[column] <= 0)
            ).sum()
        )

    validation_errors = []

    for column, count in invalid_bonds.items():
        if count > 0:
            validation_errors.append(
                f"{column}: {count} negative value(s)"
            )

    for column, count in invalid_rents.items():
        if count > 0:
            validation_errors.append(
                f"{column}: {count} non-positive value(s)"
            )

    add_log(
        log_rows,
        step="Validate numeric fields",
        decision=(
            "Checked bond counts for negative values and "
            "rent fields for non-positive values"
        ),
        reason=(
            "These checks identify logically invalid values before "
            "the data are used in later analysis."
        ),
        impact=(
            f"{sum(invalid_bonds.values())} invalid bond value(s); "
            f"{sum(invalid_rents.values())} invalid rent value(s)"
        ),
    )

    if validation_errors:
        raise ValueError(
            "Tenancy numeric validation failed: "
            + "; ".join(validation_errors)
        )


# ---------------------------------------------------------------------------
# Rent-order sanity check
# ---------------------------------------------------------------------------

def check_rent_ordering(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Check the logical ordering of the rent statistics.

    For records where all three values are available, the expected order is:

        Lower Quartile Rent <= Median Rent <= Upper Quartile Rent

    Args:
        df:
            Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Raises:
        ValueError:
            If one or more complete records violate the expected ordering.
    """
    complete_rows = (
        df[
            [
                "Lower Quartile Rent",
                "Median Rent",
                "Upper Quartile Rent",
            ]
        ]
        .notna()
        .all(axis=1)
    )

    invalid_order = (
        complete_rows
        & (
            (
                df["Lower Quartile Rent"]
                > df["Median Rent"]
            )
            |
            (
                df["Median Rent"]
                > df["Upper Quartile Rent"]
            )
        )
    )

    invalid_count = int(
        invalid_order.sum()
    )

    add_log(
        log_rows,
        step="Check rent ordering",
        decision=(
            "Checked Lower Quartile Rent <= Median Rent "
            "<= Upper Quartile Rent"
        ),
        reason=(
            "The quartile and median values should follow their "
            "expected statistical ordering."
        ),
        impact=(
            f"{invalid_count} invalid record(s) found"
        ),
    )

    if invalid_count > 0:
        raise ValueError(
            f"{invalid_count} Tenancy record(s) violate "
            "Lower Quartile Rent <= Median Rent <= Upper Quartile Rent."
        )


# ---------------------------------------------------------------------------
# Final sanity checks
# ---------------------------------------------------------------------------

def run_sanity_checks(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Run final quality-control checks before saving the cleaned dataset.

    Checks confirm that:
        - the dataset is not empty;
        - all 12 required columns remain;
        - only the expected project quarters remain;
        - every expected project quarter is represented;
        - no exact duplicate rows remain.

    These checks are useful when the script is run automatically because
    invalid output stops the pipeline before later analysis is performed.

    Args:
        df:
            Final cleaned Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Raises:
        ValueError:
            If a final sanity check fails.
    """
    if df.empty:
        raise ValueError(
            "Cleaned Tenancy dataset is empty."
        )

    missing_columns = [
        column
        for column in COLUMNS_TO_KEEP
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Required cleaned Tenancy column(s) missing: "
            f"{missing_columns}"
        )

    if len(df.columns) != len(COLUMNS_TO_KEEP):
        raise ValueError(
            "Unexpected number of columns in cleaned Tenancy dataset. "
            f"Expected {len(COLUMNS_TO_KEEP)}, found {len(df.columns)}."
        )

    unexpected_timeframes = (
        ~df["TimeFrame"].isin(
            TIMEFRAMES_TO_KEEP
        )
    )

    if unexpected_timeframes.any():
        unexpected_values = (
            df.loc[
                unexpected_timeframes,
                "TimeFrame",
            ]
            .drop_duplicates()
            .sort_values()
            .dt.strftime("%Y-%m-%d")
            .tolist()
        )

        raise ValueError(
            "Unexpected TimeFrame value(s) remain after filtering: "
            f"{unexpected_values}"
        )

    actual_timeframes = set(
        df["TimeFrame"]
        .dropna()
        .tolist()
    )

    missing_timeframes = [
        timeframe
        for timeframe in TIMEFRAMES_TO_KEEP
        if timeframe not in actual_timeframes
    ]

    if missing_timeframes:
        missing_labels = [
            timeframe.strftime("%Y-%m-%d")
            for timeframe in missing_timeframes
        ]

        raise ValueError(
            "Expected TimeFrame value(s) missing after cleaning: "
            + ", ".join(missing_labels)
        )

    remaining_duplicates = int(
        df
        .duplicated()
        .sum()
    )

    if remaining_duplicates > 0:
        raise ValueError(
            f"{remaining_duplicates} exact duplicate row(s) "
            "remain after cleaning."
        )

    add_log(
        log_rows,
        step="Final sanity checks",
        decision=(
            "Validated final columns, timeframe values, "
            "required quarters, and duplicates"
        ),
        reason=(
            "The automated pipeline should stop before saving "
            "invalid data for later analysis."
        ),
        impact=(
            f"{len(df)} final rows; "
            f"{len(df.columns)} final columns; "
            "all final sanity checks passed"
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

    The raw source dataset is never overwritten. TimeFrame is written using
    YYYY-MM-DD so that later analysis receives a consistent date format.

    Args:
        df:
            Final cleaned Tenancy DataFrame.
        log_rows:
            Cleaning-log entries.

    Raises:
        RuntimeError:
            If an expected output file is not created.
    """
    DATA_DIR.mkdir(
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

    if not OUTPUT_FILE.exists():
        raise RuntimeError(
            f"Cleaned Tenancy output was not created: "
            f"{OUTPUT_FILE}"
        )

    if not CLEANING_LOG_FILE.exists():
        raise RuntimeError(
            f"Tenancy cleaning log was not created: "
            f"{CLEANING_LOG_FILE}"
        )


# ---------------------------------------------------------------------------
# Main cleaning stage
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run the complete Tenancy cleaning stage.

    Each function performs one clearly defined task. Validation errors are
    allowed to stop execution so that an orchestration script can detect a
    failed stage instead of continuing with invalid data.
    """
    log_rows = []

    df = load_data(
        DATA_FILE
    )

    original_rows = len(
        df
    )

    original_columns = len(
        df.columns
    )

    print(
        f"Loaded Tenancy dataset: "
        f"{original_rows} rows, "
        f"{original_columns} columns"
    )

    # Fail early if the source structure has changed.
    check_expected_columns(
        df
    )

    print(
        "Input column sanity check passed."
    )

    # Keep the project columns.
    cleaned = select_columns(
        df,
        log_rows,
    )

    print(
        f"Columns retained: "
        f"{len(cleaned.columns)}"
    )

    # Parse TimeFrame and keep the project's established quarters.
    cleaned = clean_and_filter_timeframe(
        cleaned,
        log_rows,
    )

    print(
        f"Rows after timeframe filter: "
        f"{len(cleaned)}"
    )

    print(
        "\nTimeFrames retained:"
    )

    print(
        cleaned["TimeFrame"]
        .value_counts()
        .sort_index()
    )

    # Apply the remaining cleaning and validation steps.
    cleaned = standardise_text(
        cleaned,
        log_rows,
    )

    cleaned = remove_exact_duplicates(
        cleaned,
        log_rows,
    )

    document_missing_values(
        cleaned,
        log_rows,
    )

    validate_numeric_fields(
        cleaned,
        log_rows,
    )

    check_rent_ordering(
        cleaned,
        log_rows,
    )

    run_sanity_checks(
        cleaned,
        log_rows,
    )

    print(
        "\nFinal sanity checks passed."
    )

    # Save only after every validation step has succeeded.
    save_outputs(
        cleaned,
        log_rows,
    )

    print(
        "\nCleaning complete."
    )

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

    print(
        "\nMissing values remaining:"
    )

    missing = (
        cleaned
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
        print(
            "None"
        )
    else:
        print(
            missing
        )

    print(
        "\nMedian Rent summary:"
    )

    print(
        cleaned["Median Rent"]
        .describe()
    )


if __name__ == "__main__":
    main()