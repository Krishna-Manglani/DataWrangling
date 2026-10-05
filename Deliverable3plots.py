"""
Reproduce and update the earlier Airbnb exploratory analyses.

This script uses the combined Christchurch Airbnb dataset created by
process_listings.py. It automatically includes all monthly datasets that
are currently available in the combined file.

Analyses:
    1. Plot the Christchurch Airbnb price distribution.
    2. Calculate days since last review for each monthly dataset.
    3. Create a days-since-review histogram for each month.
    4. Identify the top 10% of listing-month records by number of reviews.

Automation notes:
    - No analysis months are hard-coded.
    - Months are discovered from the combined dataset.
    - Review reference dates are derived from the data.
    - Output plots are written to output_graphs/.
    - Existing project filename conventions are preserved.
    - Terminal output is kept concise for run_pipeline.py.

Input:
    listings_data/listings_christchurch_combined.csv

Outputs:
    output_graphs/price_distribution.png
    output_graphs/days_since_review_<month>_<year>.png
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

INPUT_FILE = (
    PROJECT_ROOT
    / "listings_data"
    / "listings_christchurch_combined.csv"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "output_graphs"
)

MAX_PRICE_FOR_HISTOGRAM = 1000
PRICE_BINS = 30
REVIEW_BINS = 30
TOP_REVIEW_PERCENT = 0.10

REQUIRED_COLUMNS = {
    "id",
    "name",
    "price",
    "number_of_reviews",
    "last_review",
    "year",
    "month",
    "month_year",
}

# Preserve the filename convention already used in the project.
MONTH_FILENAME_NAMES = {
    1: "jan",
    2: "feb",
    3: "march",
    4: "april",
    5: "may",
    6: "june",
    7: "july",
    8: "aug",
    9: "sept",
    10: "oct",
    11: "nov",
    12: "dec",
}


# ---------------------------------------------------------------------------
# Load and validate data
# ---------------------------------------------------------------------------

def load_data():
    """
    Load the combined Christchurch Airbnb dataset and validate the
    columns required for the Deliverable 3 analyses.
    """
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_FILE}\n"
            "Run process_listings.py first."
        )

    df = pd.read_csv(
        INPUT_FILE,
        low_memory=False,
    )

    if df.empty:
        raise ValueError(
            "The combined Airbnb dataset is empty."
        )

    missing_columns = (
        REQUIRED_COLUMNS
        - set(df.columns)
    )

    if missing_columns:
        raise ValueError(
            "The combined Airbnb dataset is missing "
            f"required columns: {sorted(missing_columns)}"
        )

    # Convert fields used for ordering and analysis.
    df["year"] = pd.to_numeric(
        df["year"],
        errors="coerce",
    )

    df["month"] = pd.to_numeric(
        df["month"],
        errors="coerce",
    )

    if df["year"].isna().any():
        raise ValueError(
            "Some rows have invalid year values."
        )

    if df["month"].isna().any():
        raise ValueError(
            "Some rows have invalid month values."
        )

    if not df["month"].between(1, 12).all():
        raise ValueError(
            "Month values must be between 1 and 12."
        )

    df["year"] = df["year"].astype(int)
    df["month"] = df["month"].astype(int)

    month_count = (
        df[["year", "month"]]
        .drop_duplicates()
        .shape[0]
    )

    print(
        f"Loaded combined Airbnb dataset: "
        f"{len(df)} rows"
    )

    print(
        f"Monthly datasets found: "
        f"{month_count}"
    )

    return df


# ---------------------------------------------------------------------------
# Price distribution
# ---------------------------------------------------------------------------

def plot_price_distribution(df):
    """
    Plot the Christchurch Airbnb price distribution.

    Missing, zero, negative, and very high prices above the configured
    plotting limit are excluded from this visualisation only. The
    underlying combined dataset is not modified.
    """
    price = pd.to_numeric(
        df["price"],
        errors="coerce",
    )

    plot_prices = price[
        price.notna()
        & (price > 0)
        & (price <= MAX_PRICE_FOR_HISTOGRAM)
    ]

    if plot_prices.empty:
        raise ValueError(
            "No valid prices are available for "
            "the price distribution plot."
        )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = (
        OUTPUT_DIR
        / "price_distribution.png"
    )

    plt.figure(
        figsize=(10, 6)
    )

    plt.hist(
        plot_prices,
        bins=PRICE_BINS,
        edgecolor="black",
    )

    plt.title(
        "Christchurch Airbnb Price Distribution"
    )

    plt.xlabel(
        "Price per Night (NZD)"
    )

    plt.ylabel(
        "Frequency"
    )

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=300,
    )

    plt.close()

    print(
        f"Saved price distribution plot to "
        f"{output_file.relative_to(PROJECT_ROOT)}"
    )


# ---------------------------------------------------------------------------
# Days since last review
# ---------------------------------------------------------------------------

def prepare_review_data(df):
    """
    Prepare valid review records and calculate days since last review.

    The simplified monthly Airbnb files do not contain the exact scrape
    date used in the earlier manual workflow. To keep this stage fully
    automated, the latest valid last_review date observed within each
    monthly dataset is used as that month's reference date.

    This produces a reproducible, data-derived review-recency measure
    without hard-coding a new reference date for every new month.
    """
    review_data = df.copy()

    review_data["last_review"] = pd.to_datetime(
        review_data["last_review"],
        errors="coerce",
    )

    review_data = review_data.dropna(
        subset=["last_review"]
    ).copy()

    if review_data.empty:
        raise ValueError(
            "No valid last_review dates are "
            "available for analysis."
        )

    # Automatically derive one reference date for each monthly dataset.
    reference_dates = (
        review_data
        .groupby("month_year")["last_review"]
        .max()
        .rename("reference_date")
    )

    review_data = review_data.join(
        reference_dates,
        on="month_year",
    )

    review_data["days_since_review"] = (
        review_data["reference_date"]
        - review_data["last_review"]
    ).dt.days

    if (
        review_data["days_since_review"]
        < 0
    ).any():
        raise ValueError(
            "Negative days_since_review values "
            "were produced."
        )

    print(
        "Review reference dates derived "
        "automatically from each monthly dataset."
    )

    return review_data


def plot_review_histograms(review_data):
    """
    Create one days-since-review histogram for every monthly dataset.

    Months are discovered automatically and ordered chronologically.
    Existing project output filename conventions are preserved.
    """
    month_order = (
        review_data[
            [
                "year",
                "month",
                "month_year",
            ]
        ]
        .drop_duplicates()
        .sort_values(
            ["year", "month"]
        )
    )

    plots_created = 0

    for row in month_order.itertuples(
        index=False
    ):
        month_year = row.month_year

        month_data = review_data[
            review_data["month_year"]
            == month_year
        ]

        if month_data.empty:
            continue

        month_number = int(
            row.month
        )

        year_number = int(
            row.year
        )

        # Use the same filename convention as the existing project:
        # jan, feb, march, april, may, june, july, aug, etc.
        month_filename = (
            MONTH_FILENAME_NAMES[
                month_number
            ]
        )

        output_file = (
            OUTPUT_DIR
            / (
                "days_since_review_"
                f"{month_filename}_"
                f"{year_number}.png"
            )
        )

        plt.figure(
            figsize=(10, 6)
        )

        plt.hist(
            month_data[
                "days_since_review"
            ],
            bins=REVIEW_BINS,
            edgecolor="black",
        )

        plt.title(
            "Days Since Last Review - "
            f"{month_year}"
        )

        plt.xlabel(
            "Days Since Last Review"
        )

        plt.ylabel(
            "Frequency"
        )

        plt.tight_layout()

        plt.savefig(
            output_file,
            dpi=300,
        )

        plt.close()

        plots_created += 1

    print(
        f"Created {plots_created} "
        "monthly days-since-review plots."
    )


# ---------------------------------------------------------------------------
# Top 10% by reviews
# ---------------------------------------------------------------------------

def report_top_reviewed_listings(df):
    """
    Identify the top 10% of listing-month records by number of reviews.

    The calculation follows the earlier Deliverable 3 analysis. The full
    Top 10% table is not printed because thousands of rows would make the
    automated pipeline output difficult to read. Instead, a concise
    summary is printed.
    """
    review_counts = df.copy()

    review_counts[
        "number_of_reviews"
    ] = pd.to_numeric(
        review_counts[
            "number_of_reviews"
        ],
        errors="coerce",
    )

    review_counts = review_counts.dropna(
        subset=["number_of_reviews"]
    ).copy()

    if review_counts.empty:
        raise ValueError(
            "No valid number_of_reviews values "
            "are available."
        )

    sorted_reviews = (
        review_counts
        .sort_values(
            "number_of_reviews",
            ascending=False,
        )
    )

    top_10_count = int(
        len(sorted_reviews)
        * TOP_REVIEW_PERCENT
    )

    if top_10_count < 1:
        raise ValueError(
            "Dataset is too small to calculate "
            "the Top 10% of listings."
        )

    top_10 = sorted_reviews.head(
        top_10_count
    )

    # Print a concise summary instead of thousands of rows.
    print(
        "\nTop 10% by number of reviews:"
    )

    print(
        f"Valid listing-month records: "
        f"{len(sorted_reviews)}"
    )

    print(
        f"Top 10% selected: "
        f"{len(top_10)} "
        "listing-month records"
    )

    print(
        "Highest number of reviews: "
        f"{top_10['number_of_reviews'].max():.0f}"
    )

    print(
        "Lowest number of reviews "
        "in Top 10%: "
        f"{top_10['number_of_reviews'].min():.0f}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    """
    Run all Deliverable 3 Airbnb analyses.
    """
    print()
    print(
        "Running Deliverable 3 "
        "Airbnb analyses..."
    )

    df = load_data()

    plot_price_distribution(
        df
    )

    review_data = prepare_review_data(
        df
    )

    plot_review_histograms(
        review_data
    )

    report_top_reviewed_listings(
        df
    )

    print()
    print(
        "Deliverable 3 analyses complete. "
        "Plots saved to output_graphs/"
    )


if __name__ == "__main__":
    main()