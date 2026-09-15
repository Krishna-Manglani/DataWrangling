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

# PRESENTATION GUIDE:
# These paths tell the script where the Deliverable 3 dataset is located
# and where the cleaned dataset and cleaning log should be saved.
#
# We save the cleaned data separately so the original Deliverable 3
# dataset is not overwritten.

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

# PRESENTATION GUIDE:
# The Deliverable 3 dataset originally contains 21 columns.
#
# We reviewed the columns and decided to retain these 19 because
# they may still be useful for the Airbnb analysis or later comparison
# with the Tenancy Services dataset.
#
# Important examples:
# - id identifies individual Airbnb listings.
# - latitude and longitude are kept for geographic analysis.
# - price is needed for Airbnb price analysis.
# - availability_365 measures yearly listing availability.
# - year, month and month_year identify the monthly snapshots.

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

# PRESENTATION GUIDE:
# We only remove columns when there is a clear reason.
#
# license:
# All values are missing, so this column provides no usable information.
#
# neighbourhood_group:
# Every row contains "Christchurch City".
# Since Deliverable 3 already filtered the dataset to Christchurch,
# this column is redundant.
#
# Therefore:
# 21 original columns - 2 removed = 19 retained original columns.

COLUMNS_TO_DROP = [
    "license",
    "neighbourhood_group",
]


# ---------------------------------------------------------------------------
# Other cleaning settings
# ---------------------------------------------------------------------------

# PRESENTATION GUIDE:
# Prices above NZD $1,000 are considered unusual enough to review.
#
# We DO NOT automatically remove them because a high Airbnb price
# could still represent a genuine listing.
#
# Instead, the code creates a flag so these observations can be
# identified and investigated later.

PRICE_REVIEW_THRESHOLD = 1000


# ---------------------------------------------------------------------------
# Cleaning log
# ---------------------------------------------------------------------------

# PRESENTATION GUIDE:
# We create a cleaning log so that every important cleaning decision
# is documented.
#
# The log records:
# - what we did,
# - why we did it,
# - and what effect it had.
#
# This makes our cleaning process transparent and reproducible.

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

# PRESENTATION GUIDE:
# We start by loading the combined Christchurch Airbnb dataset that
# was produced in Deliverable 3.
#
# We do not manually edit the CSV because using code makes the
# cleaning process reproducible.

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

# PRESENTATION GUIDE:
# Before cleaning, we confirm that all 21 expected original columns
# are actually present.
#
# This is a safety check. If the dataset structure changes, the script
# stops instead of silently performing the wrong cleaning process.

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

# PRESENTATION GUIDE:
# We remove only license and neighbourhood_group.
#
# We do NOT remove a column just because it contains some missing values.
# The other 19 columns still contain potentially useful information.
#
# Latitude and longitude are specifically retained for geographic
# analysis and later comparison.

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

# PRESENTATION GUIDE:
# We standardise selected text columns by removing leading and trailing
# spaces so that categories are represented consistently.
#
# For example:
# "Private room " and "Private room"
# should not accidentally be treated as different categories.
#
# We also convert last_review to a proper date format so it can be
# analysed consistently later.
#
# Invalid dates are changed to missing values rather than guessed.

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

# PRESENTATION GUIDE:
# We perform two types of duplicate checking.
#
# First, we check for completely identical rows.
# Exact duplicate rows provide no additional information.
#
# Second, we check id + year + month.
#
# The same Airbnb listing can legitimately appear in multiple months,
# because our dataset contains monthly snapshots.
#
# However, the same listing should not normally appear more than once
# within the same year and month.

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

# PRESENTATION GUIDE:
# We check missing values but do not automatically remove or impute them.
#
# Why?
# An incomplete record can still contain useful information.
#
# Examples:
# - A listing with missing price may still be useful for counting listings.
# - Missing review information may be legitimate for a listing with
#   no reviews.
# - Missing minimum_nights should not be guessed.
#
# Automatically deleting incomplete records could cause unnecessary
# data loss, while imputing could introduce values that were never observed.

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

# PRESENTATION GUIDE:
# We validate important numeric columns using logical rules based
# on what each variable represents.
#
# price:
# Non-missing prices should be greater than zero.
#
# availability_365:
# This represents the number of days available during one year,
# so it must be between 0 and 365.
#
# minimum_nights:
# A non-missing minimum stay should be greater than zero.
#
# latitude and longitude:
# We check that coordinates are available because they are important
# for geographic analysis.

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

    # Check for zero or negative non-missing prices.
    invalid_price = (
        cleaned["price"].notna()
        &
        (cleaned["price"] <= 0)
    ).sum()

    # Check whether availability is outside the logical 0-365 range.
    invalid_availability = (
        (cleaned["availability_365"] < 0)
        |
        (cleaned["availability_365"] > 365)
    ).sum()

    # Check for zero or negative minimum-night requirements.
    invalid_minimum_nights = (
        cleaned["minimum_nights"].notna()
        &
        (cleaned["minimum_nights"] <= 0)
    ).sum()

    # Check whether any listings are missing geographic coordinates.
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

    # -----------------------------------------------------------------------
    # Flag unusually high prices
    # -----------------------------------------------------------------------

    # PRESENTATION GUIDE:
    # We found some unusually high Airbnb prices.
    #
    # Instead of automatically deleting them, we create
    # price_review_flag.
    #
    # True  = price is above NZD $1,000.
    # False = price was not flagged.
    #
    # Our result:
    # 153 observations were flagged.
    #
    # We retain these observations because a high Airbnb price could
    # still represent a genuine listing.
    #
    # This adds ONE new column to the dataset.
    #
    # Therefore:
    # 19 retained original columns + 1 price_review_flag
    # = 20 final columns.

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

# PRESENTATION GUIDE:
# Before saving the dataset, we perform final quality-control checks.
#
# We confirm:
# - latitude and longitude are still present.
# - coordinates do not contain missing values.
# - availability_365 remains between 0 and 365.
# - no exact duplicates remain.
#
# This helps make sure our cleaning process did not accidentally
# introduce new data-quality problems.

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

# PRESENTATION GUIDE:
# We save two outputs.
#
# 1. listings_christchurch_cleaned.csv
#    This is our final cleaned Airbnb dataset.
#
# 2. listings_cleaning_log.csv
#    This records our cleaning decisions, reasons and consequences.
#
# We save the cleaned dataset separately instead of overwriting the
# Deliverable 3 dataset. This keeps the process reproducible.

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

    # -----------------------------------------------------------------------
    # Step 1: Load Deliverable 3 dataset
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "We start with the Christchurch Airbnb dataset produced in
    # Deliverable 3. It contains 28,795 rows and 21 columns."

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

    # PRESENTATION GUIDE:
    # "Before cleaning, we confirm that all 21 expected columns exist."

    check_expected_columns(
        df
    )

    # -----------------------------------------------------------------------
    # Step 2: Select columns
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "We remove license because it is completely missing and
    # neighbourhood_group because it only contains Christchurch City.
    # This leaves 19 useful original columns."

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
    # Step 3: Standardise fields
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "We remove unnecessary spaces from text fields and convert
    # last_review into a consistent date format."

    cleaned = standardise_fields(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 4: Check duplicates
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "We check exact duplicates and also whether the same listing
    # appears more than once in the same year and month."

    cleaned = check_duplicates(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 5: Check missing values
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "We document missing values instead of automatically deleting
    # or imputing them because incomplete records can still contain
    # useful information."

    check_missing_values(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 6: Validate numeric fields and price outliers
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "We check price, availability, minimum nights and coordinates
    # using logical validation rules.
    #
    # We also flag 153 prices above $1,000 for review rather than
    # automatically deleting them."

    cleaned = validate_numeric_fields(
        cleaned,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 7: Final sanity checks
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "Before saving, we check the required coordinates, availability
    # range and remaining duplicates to make sure the final dataset
    # satisfies our cleaning rules."

    run_sanity_checks(
        cleaned,
        original_rows,
        original_columns,
        log_rows,
    )

    # -----------------------------------------------------------------------
    # Step 8: Save outputs
    # -----------------------------------------------------------------------
    # PRESENTATION GUIDE:
    # "Finally, we save the cleaned dataset and a separate cleaning
    # log so our decisions are documented and reproducible."

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

    # PRESENTATION GUIDE:
    # The price summary helps us inspect the distribution and identify
    # whether there are unusually high or impossible price values.

    print("\nPrice summary:")

    print(
        cleaned["price"]
        .describe()
    )

    # PRESENTATION GUIDE:
    # availability_365 should logically range from 0 to 365.
    # The summary lets us verify that the minimum and maximum are
    # within this valid range.

    print("\nAvailability summary:")

    print(
        cleaned["availability_365"]
        .describe()
    )

    # PRESENTATION GUIDE:
    # This shows how many observations were identified by our
    # price_review_flag.
    #
    # Current result:
    # False = 28,642
    # True  = 153

    print("\nPrice values flagged for review:")

    print(
        cleaned["price_review_flag"]
        .value_counts()
    )


if __name__ == "__main__":
    main()