"""
Clean and validate the combined Christchurch Airbnb listings dataset.

This script is the second stage of the automated Airbnb data-wrangling
pipeline.

Input:
    listings_data/listings_christchurch_combined.csv

Main steps:
    1. Load the combined Christchurch Airbnb dataset.
    2. Validate the expected input columns.
    3. Keep the project columns required for later analysis.
    4. Standardise selected text and date fields.
    5. Check and remove exact duplicate rows.
    6. Check duplicate listing-month combinations.
    7. Document missing values.
    8. Validate important numeric fields.
    9. Flag unusually high prices for review.
   10. Run final sanity checks.
   11. Save the cleaned dataset and cleaning log.

Outputs:
    listings_data/listings_christchurch_cleaned.csv
    listings_data/listings_cleaning_log.csv

The cleaning decisions from Deliverable 4 are retained. The script does not
hard-code row counts or results because these change when new monthly Airbnb
datasets are added.

Run from the repository root:
    python clean_listing.py
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DATA_DIR = Path("listings_data")

DATA_FILE = DATA_DIR / "listings_christchurch_combined.csv"

OUTPUT_FILE = DATA_DIR / "listings_christchurch_cleaned.csv"

CLEANING_LOG_FILE = DATA_DIR / "listings_cleaning_log.csv"

PRICE_REVIEW_THRESHOLD = 1000

MIN_AVAILABILITY_DAYS = 0
MAX_AVAILABILITY_DAYS = 365


# These are the useful columns retained from the combined Airbnb dataset.
COLUMNS_TO_KEEP = [
    "id",
    "name",
    "host_id",
    "host_name",
    "neighbourhood",
    "latitude",
    "longitude",
    "room_type",
    "price",
    "minimum_nights",
    "number_of_reviews",
    "last_review",
    "reviews_per_month",
    "calculated_host_listings_count",
    "availability_365",
    "number_of_reviews_ltm",
    "year",
    "month",
    "month_year",
]

# These columns existed in the original monthly data but were intentionally
# excluded from the cleaned dataset in Deliverable 4.
COLUMNS_TO_DROP = [
    "license",
    "neighbourhood_group",
]

TEXT_COLUMNS = [
    "name",
    "host_name",
    "neighbourhood",
    "room_type",
    "month_year",
]

LISTING_MONTH_KEY = [
    "id",
    "year",
    "month",
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

    Each entry records the cleaning step, decision, reason, and effect on the
    dataset. This preserves the documentation approach used in Deliverable 4.

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
# Load and validate input
# ---------------------------------------------------------------------------

def load_data(filepath: Path) -> pd.DataFrame:
    """
    Load the combined Christchurch Airbnb dataset.

    Args:
        filepath:
            Path to the combined dataset produced by process_listings.py.

    Returns:
        The loaded Airbnb DataFrame.

    Raises:
        FileNotFoundError:
            If the expected combined dataset does not exist.
        ValueError:
            If the dataset is empty.
    """
    if not filepath.exists():
        raise FileNotFoundError(
            f"Could not find required input: {filepath}. "
            "Run process_listings.py first."
        )

    df = pd.read_csv(
        filepath,
        low_memory=False,
    )

    if df.empty:
        raise ValueError(
            f"Input dataset is empty: {filepath}"
        )

    return df


def check_expected_columns(df: pd.DataFrame) -> None:
    """
    Check that all columns required by the cleaning process are available.

    The automated pipeline stops if the expected input structure changes
    rather than continuing with incomplete or incorrect cleaning.

    Args:
        df:
            Combined Airbnb DataFrame.

    Raises:
        ValueError:
            If one or more required columns are missing.
    """
    expected_columns = (
        COLUMNS_TO_KEEP
        + COLUMNS_TO_DROP
    )

    missing_columns = [
        column
        for column in expected_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Required Airbnb column(s) missing: "
            f"{missing_columns}"
        )


def check_month_metadata(df: pd.DataFrame) -> None:
    """
    Validate the year and month metadata created by process_listings.py.

    The month value must be between 1 and 12 and year/month metadata must not
    be missing. This checks the interface between the first and second stages
    of the automated pipeline.

    Args:
        df:
            Combined Airbnb DataFrame.

    Raises:
        ValueError:
            If year/month values are missing or month values are invalid.
    """
    if df["year"].isna().any():
        raise ValueError(
            "Missing values found in the 'year' column."
        )

    if df["month"].isna().any():
        raise ValueError(
            "Missing values found in the 'month' column."
        )

    invalid_months = ~df["month"].between(
        1,
        12,
    )

    if invalid_months.any():
        invalid_values = sorted(
            df.loc[
                invalid_months,
                "month",
            ]
            .dropna()
            .unique()
            .tolist()
        )

        raise ValueError(
            "Invalid month value(s) found: "
            f"{invalid_values}"
        )

    if df["month_year"].isna().any():
        raise ValueError(
            "Missing values found in the 'month_year' column."
        )


# ---------------------------------------------------------------------------
# Select useful columns
# ---------------------------------------------------------------------------

def select_columns(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Keep the project columns required for later processing and analysis.

    The original Deliverable 4 cleaning decision is retained:
        - license is excluded because it contains no useful project data.
        - neighbourhood_group is excluded because the dataset has already
          been filtered to Christchurch City.

    Latitude and longitude are retained for the later SA2 matching stage.

    Args:
        df:
            Combined Airbnb DataFrame.
        log_rows:
            Cleaning-log entries.

    Returns:
        DataFrame containing the retained columns.
    """
    original_columns = len(
        df.columns
    )

    cleaned = df[
        COLUMNS_TO_KEEP
    ].copy()

    add_log(
        log_rows,
        step="Select columns",
        decision=(
            f"Kept {len(COLUMNS_TO_KEEP)} useful columns "
            f"and excluded {COLUMNS_TO_DROP}"
        ),
        reason=(
            "'license' is not required for the project and "
            "'neighbourhood_group' is redundant after filtering "
            "the data to Christchurch City."
        ),
        impact=(
            f"{original_columns} columns -> "
            f"{len(cleaned.columns)} columns"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# Standardise fields
# ---------------------------------------------------------------------------

def standardise_fields(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Standardise selected text fields and the last_review date.

    Leading and trailing whitespace is removed from selected text columns.
    last_review is converted to a datetime value. Invalid dates are converted
    to missing values rather than guessed.

    Args:
        df:
            Airbnb DataFrame after column selection.
        log_rows:
            Cleaning-log entries.

    Returns:
        DataFrame with standardised fields.
    """
    cleaned = df.copy()

    for column in TEXT_COLUMNS:
        cleaned[column] = (
            cleaned[column]
            .astype("string")
            .str.strip()
        )

    missing_before = int(
        cleaned["last_review"]
        .isna()
        .sum()
    )

    cleaned["last_review"] = pd.to_datetime(
        cleaned["last_review"],
        errors="coerce",
    )

    missing_after = int(
        cleaned["last_review"]
        .isna()
        .sum()
    )

    newly_missing = (
        missing_after
        - missing_before
    )

    add_log(
        log_rows,
        step="Standardise fields",
        decision=(
            "Trimmed selected text fields and converted "
            "last_review to datetime"
        ),
        reason=(
            "Consistent text and date formats improve validation "
            "and later analysis."
        ),
        impact=(
            f"{newly_missing} additional last_review value(s) "
            "became missing because they could not be parsed"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# Duplicate checks
# ---------------------------------------------------------------------------

def check_duplicates(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Check exact duplicates and duplicate listing-month combinations.

    Exact duplicate rows are removed because they provide no additional
    information.

    The same Airbnb listing may legitimately occur in different months.
    However, the same listing should not normally occur more than once within
    the same year and month.

    Args:
        df:
            Airbnb DataFrame.
        log_rows:
            Cleaning-log entries.

    Returns:
        DataFrame after removing exact duplicate rows.
    """
    cleaned = df.copy()

    exact_duplicates = int(
        cleaned
        .duplicated()
        .sum()
    )

    if exact_duplicates > 0:
        cleaned = (
            cleaned
            .drop_duplicates()
            .copy()
        )

    add_log(
        log_rows,
        step="Check exact duplicates",
        decision="Removed exact duplicate rows",
        reason=(
            "Completely identical rows provide no additional information."
        ),
        impact=(
            f"{exact_duplicates} row(s) removed"
        ),
    )

    listing_month_duplicates = int(
        cleaned
        .duplicated(
            subset=LISTING_MONTH_KEY
        )
        .sum()
    )

    add_log(
        log_rows,
        step="Check listing-month duplicates",
        decision=(
            "Checked duplicate combinations of id + year + month"
        ),
        reason=(
            "A listing may occur in different monthly snapshots, "
            "but should not normally occur more than once in the "
            "same monthly snapshot."
        ),
        impact=(
            f"{listing_month_duplicates} duplicate "
            "listing-month combination(s) found"
        ),
    )

    if listing_month_duplicates > 0:
        raise ValueError(
            f"Found {listing_month_duplicates} duplicate "
            "id + year + month combination(s). "
            "Check the monthly source data before continuing."
        )

    return cleaned


# ---------------------------------------------------------------------------
# Missing values
# ---------------------------------------------------------------------------

def check_missing_values(
    df: pd.DataFrame,
    log_rows: list,
) -> None:
    """
    Check and document missing values without automatically imputing them.

    Missing values are retained where appropriate because incomplete records
    can still contain useful information. For example, a listing with a
    missing price can still contribute to listing counts.

    Args:
        df:
            Cleaned Airbnb DataFrame.
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
        impact = (
            "No missing values found"
        )

    else:
        impact = "; ".join(
            f"{column}: {int(count)}"
            for column, count in missing.items()
        )

    add_log(
        log_rows,
        step="Check missing values",
        decision=(
            "Retained legitimate missing values"
        ),
        reason=(
            "Automatically deleting or imputing all missing values "
            "could remove useful records or introduce values that "
            "were not observed."
        ),
        impact=impact,
    )


# ---------------------------------------------------------------------------
# Numeric validation and price flag
# ---------------------------------------------------------------------------

def validate_numeric_fields(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Validate important numeric fields and create the price review flag.

    Checks:
        - non-missing price must be greater than zero;
        - availability_365 must be between 0 and 365;
        - non-missing minimum_nights must be greater than zero;
        - latitude and longitude must be present.

    Prices above PRICE_REVIEW_THRESHOLD are flagged rather than deleted
    because unusually high prices may still represent genuine listings.

    Args:
        df:
            Airbnb DataFrame.
        log_rows:
            Cleaning-log entries.

    Returns:
        DataFrame with price_review_flag added.

    Raises:
        ValueError:
            If logically invalid numeric values or missing coordinates
            are found.
    """
    cleaned = df.copy()

    invalid_price = int(
        (
            cleaned["price"].notna()
            & (cleaned["price"] <= 0)
        ).sum()
    )

    invalid_availability = int(
        (
            cleaned["availability_365"].notna()
            & ~cleaned["availability_365"].between(
                MIN_AVAILABILITY_DAYS,
                MAX_AVAILABILITY_DAYS,
            )
        ).sum()
    )

    invalid_minimum_nights = int(
        (
            cleaned["minimum_nights"].notna()
            & (cleaned["minimum_nights"] <= 0)
        ).sum()
    )

    missing_coordinates = int(
        (
            cleaned["latitude"].isna()
            | cleaned["longitude"].isna()
        ).sum()
    )

    add_log(
        log_rows,
        step="Validate numeric fields",
        decision=(
            "Checked price, availability_365, minimum_nights, "
            "latitude, and longitude"
        ),
        reason=(
            "Domain-based checks identify impossible or invalid "
            "values before later pipeline stages use the data."
        ),
        impact=(
            f"invalid price={invalid_price}; "
            f"invalid availability_365={invalid_availability}; "
            f"invalid minimum_nights={invalid_minimum_nights}; "
            f"missing coordinates={missing_coordinates}"
        ),
    )

    validation_errors = []

    if invalid_price > 0:
        validation_errors.append(
            f"{invalid_price} non-positive price value(s)"
        )

    if invalid_availability > 0:
        validation_errors.append(
            f"{invalid_availability} invalid availability_365 value(s)"
        )

    if invalid_minimum_nights > 0:
        validation_errors.append(
            f"{invalid_minimum_nights} non-positive minimum_nights value(s)"
        )

    if missing_coordinates > 0:
        validation_errors.append(
            f"{missing_coordinates} row(s) with missing coordinates"
        )

    if validation_errors:
        raise ValueError(
            "Numeric validation failed: "
            + "; ".join(validation_errors)
        )

    cleaned["price_review_flag"] = (
        cleaned["price"].notna()
        & (
            cleaned["price"]
            > PRICE_REVIEW_THRESHOLD
        )
    )

    flagged_prices = int(
        cleaned["price_review_flag"]
        .sum()
    )

    add_log(
        log_rows,
        step="Check price outliers",
        decision=(
            f"Flagged prices above NZD {PRICE_REVIEW_THRESHOLD}"
        ),
        reason=(
            "An unusually high Airbnb price may still represent a "
            "genuine listing, so it is flagged for review rather "
            "than automatically deleted."
        ),
        impact=(
            f"{flagged_prices} row(s) flagged; 0 rows removed"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# Final sanity checks
# ---------------------------------------------------------------------------

def run_sanity_checks(
    df: pd.DataFrame,
    original_rows: int,
    original_columns: int,
    log_rows: list,
) -> None:
    """
    Run final quality-control checks before saving the cleaned dataset.

    The checks confirm that:
        - the dataset is not empty;
        - required geographic columns remain present;
        - coordinates are complete;
        - availability_365 remains within its valid range;
        - no exact duplicates remain;
        - no duplicate listing-month combinations remain;
        - price_review_flag exists;
        - year and month metadata remain valid.

    Args:
        df:
            Final cleaned Airbnb DataFrame.
        original_rows:
            Number of rows before cleaning.
        original_columns:
            Number of columns before cleaning.
        log_rows:
            Cleaning-log entries.

    Raises:
        ValueError:
            If any final sanity check fails.
    """
    if df.empty:
        raise ValueError(
            "Cleaned Airbnb dataset is empty."
        )

    required_final_columns = [
        "latitude",
        "longitude",
        "year",
        "month",
        "month_year",
        "price_review_flag",
    ]

    missing_final_columns = [
        column
        for column in required_final_columns
        if column not in df.columns
    ]

    if missing_final_columns:
        raise ValueError(
            "Required cleaned column(s) missing: "
            f"{missing_final_columns}"
        )

    if df["latitude"].isna().any():
        raise ValueError(
            "Missing latitude values found after cleaning."
        )

    if df["longitude"].isna().any():
        raise ValueError(
            "Missing longitude values found after cleaning."
        )

    invalid_availability = (
        df["availability_365"].notna()
        & ~df["availability_365"].between(
            MIN_AVAILABILITY_DAYS,
            MAX_AVAILABILITY_DAYS,
        )
    )

    if invalid_availability.any():
        raise ValueError(
            "availability_365 contains values outside 0-365."
        )

    exact_duplicates = int(
        df
        .duplicated()
        .sum()
    )

    if exact_duplicates > 0:
        raise ValueError(
            f"{exact_duplicates} exact duplicate row(s) remain."
        )

    listing_month_duplicates = int(
        df
        .duplicated(
            subset=LISTING_MONTH_KEY
        )
        .sum()
    )

    if listing_month_duplicates > 0:
        raise ValueError(
            f"{listing_month_duplicates} duplicate listing-month "
            "combination(s) remain."
        )

    check_month_metadata(
        df
    )

    add_log(
        log_rows,
        step="Final sanity checks",
        decision=(
            "Checked final structure, ranges, duplicates, "
            "coordinates, and month metadata"
        ),
        reason=(
            "Final validation prevents an invalid cleaned dataset "
            "from being passed to later automated pipeline stages."
        ),
        impact=(
            f"rows: {original_rows} -> {len(df)}; "
            f"columns: {original_columns} -> {len(df.columns)}; "
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
    Save the cleaned Airbnb dataset and cleaning log.

    The cleaned dataset is written separately from the combined input so the
    previous pipeline stage is not overwritten.

    Args:
        df:
            Final cleaned Airbnb DataFrame.
        log_rows:
            Cleaning-log entries.

    Raises:
        RuntimeError:
            If either expected output file is not created.
    """
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df = df.copy()

    output_df["last_review"] = (
        output_df["last_review"]
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
            f"Cleaned Airbnb output was not created: {OUTPUT_FILE}"
        )

    if not CLEANING_LOG_FILE.exists():
        raise RuntimeError(
            f"Cleaning log was not created: {CLEANING_LOG_FILE}"
        )


# ---------------------------------------------------------------------------
# Main cleaning stage
# ---------------------------------------------------------------------------

def main() -> None:
    """
    Run the complete Airbnb cleaning stage.

    Each cleaning function performs one defined task. Errors are allowed to
    stop the script so that the later orchestration script can detect a
    failed pipeline stage rather than continuing with invalid data.
    """
    log_rows = []

    # Load the output produced by process_listings.py.
    df = load_data(
        DATA_FILE
    )

    original_rows = len(df)
    original_columns = len(
        df.columns
    )

    print(
        f"Loaded dataset: "
        f"{original_rows} rows, "
        f"{original_columns} columns"
    )

    # Validate the interface between process_listings.py and this stage.
    check_expected_columns(
        df
    )

    check_month_metadata(
        df
    )

    print(
        "Input sanity checks passed."
    )

    # Keep the columns required for later stages.
    cleaned = select_columns(
        df,
        log_rows,
    )

    print(
        f"Columns retained: {len(COLUMNS_TO_KEEP)}"
    )

    # Standardise text and date fields.
    cleaned = standardise_fields(
        cleaned,
        log_rows,
    )

    # Remove exact duplicates and check listing-month uniqueness.
    cleaned = check_duplicates(
        cleaned,
        log_rows,
    )

    # Record missing values without automatically imputing them.
    check_missing_values(
        cleaned,
        log_rows,
    )

    # Validate numeric fields and create the price review flag.
    cleaned = validate_numeric_fields(
        cleaned,
        log_rows,
    )

    # Validate the final cleaned dataset before writing it.
    run_sanity_checks(
        cleaned,
        original_rows,
        original_columns,
        log_rows,
    )

    print(
        "Final sanity checks passed."
    )

    # Save the cleaned data and cleaning log.
    save_outputs(
        cleaned,
        log_rows,
    )

    print(
        "\nCleaning complete."
    )

    print(
        f"Input dataset: "
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

    remaining_missing = (
        cleaned
        .isna()
        .sum()
    )

    remaining_missing = (
        remaining_missing[
            remaining_missing > 0
        ]
        .sort_values(
            ascending=False
        )
    )

    if remaining_missing.empty:
        print(
            "None"
        )
    else:
        print(
            remaining_missing
        )

    print(
        "\nPrice summary:"
    )

    print(
        cleaned["price"]
        .describe()
    )

    print(
        "\nAvailability summary:"
    )

    print(
        cleaned["availability_365"]
        .describe()
    )

    print(
        "\nPrice values flagged for review:"
    )

    print(
        cleaned["price_review_flag"]
        .value_counts(
            dropna=False
        )
    )


if __name__ == "__main__":
    main()