"""
Deliverable 4: Clean the Christchurch Airbnb listings dataset.

Pipeline:
  1. Load the Christchurch dataset created in Deliverable 3.
  2. Record the original number of rows and columns.
  3. Keep useful columns and drop unnecessary columns.
  4. Standardise selected text and date fields.
  5. Check for duplicate records.
  6. Check missing values.
  7. Validate important numeric fields.
  8. Check and flag unusual price values.
  9. Run final sanity checks.
 10. Save the cleaned dataset and cleaning log.

Expected input:
  listings_data/listings_christchurch_oct25_jun26.csv

Outputs:
  listings_data/listings_christchurch_cleaned.csv
  listings_data/listings_cleaning_log.csv
"""

from pathlib import Path

import pandas as pd


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DATA_FILE = Path(
    "listings_data/listings_christchurch_oct25_jun26.csv"
)

OUTPUT_FILE = Path(
    "listings_data/listings_christchurch_cleaned.csv"
)

CLEANING_LOG_FILE = Path(
    "listings_data/listings_cleaning_log.csv"
)


# ---------------------------------------------------------------------------
# Columns to keep
# ---------------------------------------------------------------------------

# These columns are useful for the current Airbnb analysis
# and the later comparison with the Tenancy Services dataset.

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


# ---------------------------------------------------------------------------
# Columns to drop
# ---------------------------------------------------------------------------

# license:
#   All values are missing, so the column provides no useful information.
#
# neighbourhood_group:
#   Every row contains "Christchurch City" because Deliverable 3 already
#   filtered the dataset to Christchurch. The column is therefore redundant.

COLUMNS_TO_DROP = [
    "license",
    "neighbourhood_group",
]


# ---------------------------------------------------------------------------
# Other cleaning settings
# ---------------------------------------------------------------------------

# Prices above this value are flagged for review.
# They are NOT automatically removed because a high Airbnb price
# may still represent a genuine listing.

PRICE_REVIEW_THRESHOLD = 1000


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

    Each entry records:
      - what cleaning step was performed,
      - what decision was made,
      - why the decision was made,
      - what effect it had on the dataset.

    This helps document the decisions, reasons, and consequences
    required for Deliverable 4.
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
    Load the combined Christchurch Airbnb dataset from Deliverable 3.

    The script stops with an error if the expected input file cannot
    be found.
    """
    if not filepath.exists():
        raise FileNotFoundError(
            f"Could not find {filepath}. "
            "Run Deliverable 3 first or check the file location."
        )

    df = pd.read_csv(
        filepath,
        low_memory=False,
    )

    return df


# ---------------------------------------------------------------------------
# Check expected columns
# ---------------------------------------------------------------------------

def check_expected_columns(df: pd.DataFrame) -> None:
    """
    Check that the expected columns are present before cleaning.

    This prevents the cleaning process from continuing if the structure
    of the Deliverable 3 dataset has unexpectedly changed.
    """
    expected_columns = (
        COLUMNS_TO_KEEP +
        COLUMNS_TO_DROP
    )

    missing_columns = [
        col
        for col in expected_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "The following expected columns are missing: "
            f"{missing_columns}"
        )


# ---------------------------------------------------------------------------
# Select useful columns
# ---------------------------------------------------------------------------

def select_columns(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Keep useful project columns and remove unnecessary columns.

    The Deliverable 3 dataset contains 21 columns.

    Nineteen original columns are retained because they may be useful
    for the Airbnb analysis or later comparison with the Tenancy
    Services dataset.

    Two columns are removed:
      - license: all values are missing.
      - neighbourhood_group: every value is Christchurch City.

    Latitude and longitude are retained because Deliverable 4
    explicitly requires them.
    """
    original_columns = len(df.columns)

    cleaned = df[
        COLUMNS_TO_KEEP
    ].copy()

    add_log(
        log_rows,
        step="Select columns",
        decision=(
            f"Kept {len(COLUMNS_TO_KEEP)} useful columns "
            f"and dropped {COLUMNS_TO_DROP}"
        ),
        reason=(
            "'license' contains only missing values and "
            "'neighbourhood_group' contains only "
            "'Christchurch City', making both columns "
            "uninformative for the cleaned dataset."
        ),
        impact=(
            f"{original_columns} columns -> "
            f"{len(cleaned.columns)} columns; "
            f"{len(COLUMNS_TO_DROP)} columns removed"
        ),
    )

    return cleaned


# ---------------------------------------------------------------------------
# Standardise text and date fields
# ---------------------------------------------------------------------------

def standardise_fields(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Standardise selected text and date fields.

    Leading and trailing spaces are removed from selected text columns.

    The last_review column is converted to a datetime type so that
    review dates have a consistent format and can be used correctly
    in later calculations.

    Invalid dates are converted to missing values rather than guessed.
    """
    cleaned = df.copy()

    text_columns = [
        "name",
        "host_name",
        "neighbourhood",
        "room_type",
        "month_year",
    ]

    for col in text_columns:
        cleaned[col] = (
            cleaned[col]
            .astype("string")
            .str.strip()
        )

    before_missing = (
        cleaned["last_review"]
        .isna()
        .sum()
    )

    cleaned["last_review"] = pd.to_datetime(
        cleaned["last_review"],
        errors="coerce",
    )

    after_missing = (
        cleaned["last_review"]
        .isna()
        .sum()
    )

    newly_missing = (
        after_missing -
        before_missing
    )

    add_log(
        log_rows,
        step="Standardise fields",
        decision=(
            "Trimmed selected text fields and converted "
            "'last_review' to datetime"
        ),
        reason=(
            "Consistent text and date formats make the dataset "
            "easier to validate and analyse."
        ),
        impact=(
            f"{newly_missing} additional last_review value(s) "
            "became missing because they could not be parsed"
        ),
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
    Check for true duplicate records.

    Exact duplicate rows are removed if they exist.

    The same Airbnb listing can legitimately appear in different
    monthly snapshots. Therefore, duplicate listing IDs alone are
    not removed.

    The script also checks whether the same listing appears more than
    once in the same year and month using:
      id + year + month
    """
    cleaned = df.copy()

    exact_duplicates = (
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
            "Completely identical rows provide no additional "
            "information."
        ),
        impact=(
            f"{exact_duplicates} row(s) removed"
        ),
    )

    listing_month_duplicates = (
        cleaned
        .duplicated(
            subset=[
                "id",
                "year",
                "month",
            ]
        )
        .sum()
    )

    add_log(
        log_rows,
        step="Check listing-month duplicates",
        decision=(
            "Checked duplicate combinations of "
            "id + year + month"
        ),
        reason=(
            "The same listing may appear in different months, "
            "but should not normally appear more than once "
            "within the same monthly snapshot."
        ),
        impact=(
            f"{listing_month_duplicates} duplicate "
            "listing-month combination(s) found"
        ),
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
    Check and document missing values.

    Missing values are not automatically deleted or imputed.

    In particular:
      - Missing prices are retained because the listing may still
        be useful when counting available properties.
      - Missing review information can be legitimate for listings
        that have not received reviews.
      - Missing minimum_nights values are not guessed.

    This avoids unnecessary data loss and avoids creating values
    that were not present in the original dataset.
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
        decision=(
            "Retained legitimate missing values"
        ),
        reason=(
            "Automatically deleting or imputing all missing "
            "values could remove valid listings or introduce "
            "values that were not actually observed."
        ),
        impact=impact,
    )


# ---------------------------------------------------------------------------
# Validate numeric fields
# ---------------------------------------------------------------------------

def validate_numeric_fields(
    df: pd.DataFrame,
    log_rows: list,
) -> pd.DataFrame:
    """
    Validate important numeric fields.

    The following checks are performed:
      - price should be greater than zero when present.
      - availability_365 should be between 0 and 365.
      - minimum_nights should be greater than zero when present.
      - latitude and longitude should not be missing.

    Unusually high prices are flagged for review rather than
    automatically removed.
    """
    cleaned = df.copy()

    invalid_price = (
        cleaned["price"].notna()
        &
        (cleaned["price"] <= 0)
    ).sum()

    invalid_availability = (
        (cleaned["availability_365"] < 0)
        |
        (cleaned["availability_365"] > 365)
    ).sum()

    invalid_minimum_nights = (
        cleaned["minimum_nights"].notna()
        &
        (cleaned["minimum_nights"] <= 0)
    ).sum()

    missing_coordinates = (
        cleaned["latitude"].isna()
        |
        cleaned["longitude"].isna()
    ).sum()

    add_log(
        log_rows,
        step="Validate numeric fields",
        decision=(
            "Checked price, availability_365, "
            "minimum_nights, latitude, and longitude"
        ),
        reason=(
            "Domain-based checks help identify values that "
            "may be impossible or invalid."
        ),
        impact=(
            f"invalid price={invalid_price}; "
            f"invalid availability_365={invalid_availability}; "
            f"invalid minimum_nights={invalid_minimum_nights}; "
            f"missing coordinates={missing_coordinates}"
        ),
    )

    # Flag unusually high prices.
    # Do not delete them automatically because they may be genuine.

    cleaned["price_review_flag"] = (
        cleaned["price"].notna()
        &
        (
            cleaned["price"] >
            PRICE_REVIEW_THRESHOLD
        )
    )

    flagged_prices = (
        cleaned["price_review_flag"]
        .sum()
    )

    add_log(
        log_rows,
        step="Check price outliers",
        decision=(
            f"Flagged prices above NZD "
            f"{PRICE_REVIEW_THRESHOLD}"
        ),
        reason=(
            "An unusually high Airbnb price may still represent "
            "a genuine listing, so it should be investigated "
            "rather than automatically deleted."
        ),
        impact=(
            f"{flagged_prices} row(s) flagged; "
            "0 rows removed"
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
    Run final checks after cleaning.

    These checks confirm that:
      - latitude and longitude are still available,
      - latitude and longitude contain no missing values,
      - availability_365 remains within its valid range,
      - no exact duplicate rows remain,
      - the final dataset dimensions can be compared with the
        original dataset.
    """
    assert "latitude" in df.columns
    assert "longitude" in df.columns

    assert df["latitude"].notna().all(), (
        "Missing latitude values found."
    )

    assert df["longitude"].notna().all(), (
        "Missing longitude values found."
    )

    assert (
        df["availability_365"]
        .between(0, 365)
        .all()
    ), (
        "availability_365 contains values "
        "outside the range 0-365."
    )

    remaining_duplicates = (
        df
        .duplicated()
        .sum()
    )

    add_log(
        log_rows,
        step="Final sanity checks",
        decision=(
            "Checked required columns, valid ranges, "
            "and remaining duplicates"
        ),
        reason=(
            "Final checks help identify errors that survived "
            "the cleaning process or were introduced during cleaning."
        ),
        impact=(
            f"rows: {original_rows} -> {len(df)}; "
            f"columns: {original_columns} -> {len(df.columns)}; "
            f"remaining exact duplicates={remaining_duplicates}"
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
    Save the cleaned dataset and cleaning log.

    The cleaned dataset is saved separately from the Deliverable 3
    dataset so that the original processed dataset is not overwritten.

    The cleaning log records the decisions, reasons, and consequences
    of the cleaning process.
    """
    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_df = df.copy()

    # Save last_review in a consistent YYYY-MM-DD format.

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


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def main():
    """
    Run the complete Deliverable 4 Airbnb cleaning pipeline.

    The main function performs each cleaning step in order and prints
    important results so that the team can inspect and explain what
    happened during the cleaning process.
    """

    log_rows = []

    # Step 1: Load Deliverable 3 dataset.

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

    # Check that all 21 expected original columns exist.

    check_expected_columns(
        df
    )

    # Step 2: Keep useful columns and remove unnecessary columns.

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

    # Step 3: Standardise text and date fields.

    cleaned = standardise_fields(
        cleaned,
        log_rows,
    )

    # Step 4: Check duplicate records.

    cleaned = check_duplicates(
        cleaned,
        log_rows,
    )

    # Step 5: Check missing values.

    check_missing_values(
        cleaned,
        log_rows,
    )

    # Step 6: Validate numeric fields and flag unusual prices.

    cleaned = validate_numeric_fields(
        cleaned,
        log_rows,
    )

    # Step 7: Run final sanity checks.

    run_sanity_checks(
        cleaned,
        original_rows,
        original_columns,
        log_rows,
    )

    # Step 8: Save the cleaned dataset and cleaning log.

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

    print(
        cleaned
        .isna()
        .sum()
        .loc[
            lambda x: x > 0
        ]
        .sort_values(
            ascending=False
        )
    )

    print("\nPrice summary:")

    print(
        cleaned["price"]
        .describe()
    )

    print("\nAvailability summary:")

    print(
        cleaned["availability_365"]
        .describe()
    )

    print("\nPrice values flagged for review:")

    print(
        cleaned["price_review_flag"]
        .value_counts()
    )


if __name__ == "__main__":
    main()