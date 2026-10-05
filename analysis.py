"""
Analyse the cleaned Christchurch Airbnb and Tenancy Services datasets after
Airbnb listings have been enriched with Stats NZ SA2 area codes.

The analysis automatically works with newly added Airbnb months. Airbnb
months are converted to calendar quarters from their year and month rather
than using a manually maintained month-to-quarter mapping.

Where Airbnb and tenancy data are compared, only quarters available in both
datasets are used. This allows newer Airbnb months to remain in the dataset
without incorrectly assuming that matching tenancy data are available.

Inputs:
    listings_data/listings_christchurch_with_area.csv
    tenancy_data/tenancy_cleaned.csv

Analysis:
    Q1. Median Airbnb nightly price in Christchurch Central.
    Q2. Areas with the largest gap between weekly-equivalent Airbnb prices
        and weekly median long-term rent.
    Q3. Airbnb listing counts compared with active rental bond counts by area.

Outputs:
    Printed answers for the three analysis questions.

    output_graphs/q2_price_gap_top_areas.png
    output_graphs/q2_price_gap_distribution.png
    output_graphs/q3_airbnb_vs_bonds_counts.png

Run from the repository root:
    python analysis.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LISTINGS_FILE = Path(
    "listings_data/listings_christchurch_with_area.csv"
)

TENANCY_FILE = Path(
    "tenancy_data/tenancy_cleaned.csv"
)

OUT_DIR = Path("output_graphs")

CHCH_CENTRAL_AREA_CODE = 326600

# Areas with fewer matched listings are excluded from the Q2 ranking
# because their median price gap may be based on too little Airbnb data.
MIN_LISTINGS_PER_AREA = 5

TOP_GAP_AREAS = 15
TOP_DISTRIBUTION_AREAS = 8
TOP_COUNT_AREAS = 15


# ---------------------------------------------------------------------------
# Load Airbnb data
# ---------------------------------------------------------------------------

def load_listings():
    """
    Load and validate the SA2-enriched Airbnb dataset.

    A quarter_start field is derived automatically from year and month so
    newly added Airbnb months do not require changes to the source code.
    """
    if not LISTINGS_FILE.exists():
        raise FileNotFoundError(
            f"Airbnb input file not found: {LISTINGS_FILE}"
        )

    listings = pd.read_csv(
        LISTINGS_FILE,
        low_memory=False,
    )

    if listings.empty:
        raise ValueError(
            "Airbnb input dataset is empty."
        )

    required_columns = {
        "id",
        "price",
        "year",
        "month",
        "area_code",
        "area_name",
    }

    missing_columns = (
        required_columns
        - set(listings.columns)
    )

    if missing_columns:
        raise ValueError(
            "Airbnb data is missing required column(s): "
            f"{sorted(missing_columns)}"
        )

    # Convert year and month to numeric before constructing dates.
    listings["year"] = pd.to_numeric(
        listings["year"],
        errors="coerce",
    )

    listings["month"] = pd.to_numeric(
        listings["month"],
        errors="coerce",
    )

    if listings[["year", "month"]].isna().any().any():
        raise ValueError(
            "Airbnb data contains invalid year or month values."
        )

    if not listings["month"].between(1, 12).all():
        raise ValueError(
            "Airbnb data contains month values outside 1-12."
        )

    # Automatically derive the calendar quarter.
    month_dates = pd.to_datetime(
        {
            "year": listings["year"].astype(int),
            "month": listings["month"].astype(int),
            "day": 1,
        }
    )

    listings["quarter_start"] = (
        month_dates
        .dt.to_period("Q")
        .dt.start_time
        .dt.strftime("%Y-%m-%d")
    )

    listings["area_code"] = pd.to_numeric(
        listings["area_code"],
        errors="coerce",
    ).astype("Int64")

    print(
        f"Loaded Airbnb data: "
        f"{len(listings)} rows"
    )

    print(
        "Airbnb period:",
        month_dates.min().strftime("%b %Y"),
        "to",
        month_dates.max().strftime("%b %Y"),
    )

    print(
        "Airbnb quarters:",
        ", ".join(
            sorted(
                listings["quarter_start"].unique()
            )
        ),
    )

    return listings


# ---------------------------------------------------------------------------
# Load tenancy data
# ---------------------------------------------------------------------------

def load_tenancy_overall():
    """
    Load and validate the cleaned tenancy dataset.

    Only overall records where Dwelling Type and Number Of Beds are both
    'ALL' are retained so each SA2/quarter has an overall rental measure.
    """
    if not TENANCY_FILE.exists():
        raise FileNotFoundError(
            f"Tenancy input file not found: {TENANCY_FILE}"
        )

    tenancy = pd.read_csv(
        TENANCY_FILE,
        low_memory=False,
    )

    if tenancy.empty:
        raise ValueError(
            "Tenancy input dataset is empty."
        )

    required_columns = {
        "Location Id",
        "Dwelling Type",
        "Number Of Beds",
        "TimeFrame",
        "Median Rent",
        "Total Bonds",
        "Active Bonds",
        "Closed Bonds",
    }

    missing_columns = (
        required_columns
        - set(tenancy.columns)
    )

    if missing_columns:
        raise ValueError(
            "Tenancy data is missing required column(s): "
            f"{sorted(missing_columns)}"
        )

    # Remove rows without a valid Stats NZ location code.
    tenancy = tenancy[
        tenancy["Location Id"].notna()
        & (tenancy["Location Id"] != -99)
    ].copy()

    tenancy["area_code"] = (
        pd.to_numeric(
            tenancy["Location Id"],
            errors="coerce",
        )
        .astype("Int64")
    )

    tenancy["TimeFrame"] = pd.to_datetime(
        tenancy["TimeFrame"],
        errors="coerce",
    )

    if tenancy["TimeFrame"].isna().any():
        raise ValueError(
            "Tenancy data contains invalid TimeFrame values."
        )

    overall = tenancy[
        (tenancy["Dwelling Type"] == "ALL")
        & (tenancy["Number Of Beds"] == "ALL")
    ].copy()

    if overall.empty:
        raise ValueError(
            "No overall tenancy records were found "
            "(Dwelling Type=ALL, Number Of Beds=ALL)."
        )

    overall["quarter_start"] = (
        overall["TimeFrame"]
        .dt.strftime("%Y-%m-%d")
    )

    overall = overall[
        [
            "area_code",
            "quarter_start",
            "Median Rent",
            "Total Bonds",
            "Active Bonds",
            "Closed Bonds",
        ]
    ].copy()

    # There should be only one overall tenancy record for each
    # area and quarter.
    duplicates = overall.duplicated(
        ["area_code", "quarter_start"]
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate overall tenancy records found "
            "for the same area and quarter."
        )

    print(
        f"Loaded overall tenancy data: "
        f"{len(overall)} rows"
    )

    print(
        "Tenancy quarters:",
        ", ".join(
            sorted(
                overall["quarter_start"].unique()
            )
        ),
    )

    return overall


# ---------------------------------------------------------------------------
# Find periods available in both datasets
# ---------------------------------------------------------------------------

def get_common_quarters(listings, tenancy):
    """
    Return quarters that are available in both Airbnb and tenancy data.

    New Airbnb quarters without matching tenancy data are kept for
    Airbnb-only analysis but excluded from cross-dataset comparisons.
    """
    airbnb_quarters = set(
        listings["quarter_start"].dropna()
    )

    tenancy_quarters = set(
        tenancy["quarter_start"].dropna()
    )

    common_quarters = sorted(
        airbnb_quarters
        & tenancy_quarters
    )

    if not common_quarters:
        raise ValueError(
            "No overlapping Airbnb and tenancy quarters were found."
        )

    airbnb_only = sorted(
        airbnb_quarters
        - tenancy_quarters
    )

    print(
        "\nCommon Airbnb/Tenancy quarters:",
        ", ".join(common_quarters),
    )

    if airbnb_only:
        print(
            "Note: Airbnb quarter(s) without matching tenancy data:",
            ", ".join(airbnb_only),
        )

        print(
            "These Airbnb records remain available for Airbnb-only "
            "analysis but are excluded from Airbnb/Tenancy comparisons."
        )

    return common_quarters


# ---------------------------------------------------------------------------
# Q1
# ---------------------------------------------------------------------------

def q1_median_price_cc_central(listings):
    """
    Calculate the median nightly Airbnb price in Christchurch Central.

    All currently available Airbnb months are used because this question
    does not depend on the tenancy dataset.
    """
    central = listings[
        listings["area_code"]
        == CHCH_CENTRAL_AREA_CODE
    ].copy()

    if central.empty:
        raise ValueError(
            "No Airbnb records found for Christchurch Central."
        )

    valid_prices = central[
        central["price"].notna()
    ]

    if valid_prices.empty:
        raise ValueError(
            "Christchurch Central has no valid Airbnb prices."
        )

    median_price = valid_prices[
        "price"
    ].median()

    print(
        f"\nQ1: Median Airbnb price in Christchurch Central "
        f"({CHCH_CENTRAL_AREA_CODE}, "
        f"n={len(valid_prices)} priced listing-months): "
        f"${median_price:.2f}/night"
    )

    return median_price


# ---------------------------------------------------------------------------
# Q2
# ---------------------------------------------------------------------------

def q2_price_gap(
    listings,
    tenancy,
    common_quarters,
):
    """
    Compare Airbnb and long-term rental prices for overlapping quarters.

    Airbnb nightly prices are converted to a weekly equivalent and compared
    with Tenancy Services median weekly rent for the same SA2 and quarter.
    """
    comparable_airbnb = listings[
        listings["quarter_start"].isin(
            common_quarters
        )
    ].copy()

    comparable_tenancy = tenancy[
        tenancy["quarter_start"].isin(
            common_quarters
        )
    ].copy()

    merged = comparable_airbnb.merge(
        comparable_tenancy,
        on=[
            "area_code",
            "quarter_start",
        ],
        how="inner",
        validate="many_to_one",
    )

    if merged.empty:
        raise ValueError(
            "Sanity check failed: no Airbnb and tenancy "
            "records matched by area code and quarter."
        )

    matched_quarters = sorted(
        merged["quarter_start"].unique()
    )

    print(
        "\nQ2 comparison quarters:",
        ", ".join(matched_quarters),
    )

    print(
        f"Matched Airbnb/Tenancy rows: "
        f"{len(merged)}"
    )

    # Missing Airbnb prices remain missing rather than being imputed.
    merged["weekly_equiv_price"] = (
        merged["price"] * 7
    )

    merged["gap"] = (
        merged["weekly_equiv_price"]
        - merged["Median Rent"]
    )

    # Count unique Airbnb listings rather than repeated listing-month rows
    # when deciding whether an area has enough data for the ranking.
    counts = (
        merged.groupby("area_code")["id"]
        .nunique()
    )

    valid_areas = counts[
        counts >= MIN_LISTINGS_PER_AREA
    ].index

    valid = merged[
        merged["area_code"].isin(
            valid_areas
        )
    ].copy()

    if valid.empty:
        raise ValueError(
            "No areas have enough matched Airbnb listings "
            "for the Q2 comparison."
        )

    by_area = (
        valid
        .groupby(
            [
                "area_code",
                "area_name",
            ]
        )["gap"]
        .median()
        .dropna()
        .reset_index()
        .sort_values(
            "gap",
            ascending=False,
        )
    )

    if by_area.empty:
        raise ValueError(
            "Q2 produced no valid area-level price gaps."
        )

    print(
        f"\nQ2: {len(by_area)} areas with >= "
        f"{MIN_LISTINGS_PER_AREA} matched unique Airbnb listings "
        f"(of {merged['area_code'].nunique()} matched areas total)"
    )

    print(
        "Top 5 largest gap "
        "(short-term price >> long-term rent):"
    )

    print(
        by_area
        .head(5)
        .to_string(index=False)
    )

    print(
        "Top 5 smallest / most negative gap:"
    )

    print(
        by_area
        .tail(5)
        .to_string(index=False)
    )

    # Plot 1: areas with the largest median price gap.
    top_areas = by_area.head(
        TOP_GAP_AREAS
    )

    fig, ax = plt.subplots(
        figsize=(9, 6)
    )

    ax.barh(
        top_areas["area_name"],
        top_areas["gap"],
    )

    ax.set_xlabel(
        "Median (short-term weekly-equivalent $ "
        "− long-term weekly rent $)"
    )

    ax.set_title(
        "Areas with the largest short-term vs "
        "long-term rental price gap"
    )

    ax.invert_yaxis()

    fig.tight_layout()

    fig.savefig(
        OUT_DIR / "q2_price_gap_top_areas.png",
        dpi=150,
    )

    plt.close(fig)

    # Plot 2: distribution of individual price gaps for the
    # highest-gap areas.
    top_codes = (
        by_area
        .head(TOP_DISTRIBUTION_AREAS)
        ["area_code"]
    )

    plot_data = [
        valid.loc[
            valid["area_code"] == code,
            "gap",
        ].dropna()
        for code in top_codes
    ]

    labels = [
        by_area.loc[
            by_area["area_code"] == code,
            "area_name",
        ].iloc[0]
        for code in top_codes
    ]

    fig, ax = plt.subplots(
        figsize=(10, 6)
    )

    ax.boxplot(
        plot_data,
        tick_labels=labels,
        vert=False,
    )

    ax.set_xlabel(
        "Weekly-equivalent short-term $ "
        "− long-term rent $"
    )

    ax.set_title(
        "Distribution of the price gap, "
        "top 8 areas by median gap"
    )

    fig.tight_layout()

    fig.savefig(
        OUT_DIR / "q2_price_gap_distribution.png",
        dpi=150,
    )

    plt.close(fig)

    return by_area


# ---------------------------------------------------------------------------
# Q3
# ---------------------------------------------------------------------------

def q3_counts_comparison(
    listings,
    tenancy,
    common_quarters,
):
    """
    Compare unique Airbnb listings with active rental bonds by area.

    Both datasets use the latest quarter available in both sources so the
    counts refer to the same time period.
    """
    latest_quarter = max(
        common_quarters
    )

    airbnb_latest = listings[
        listings["quarter_start"]
        == latest_quarter
    ].copy()

    tenancy_latest = tenancy[
        tenancy["quarter_start"]
        == latest_quarter
    ].copy()

    if airbnb_latest.empty:
        raise ValueError(
            f"No Airbnb records found for {latest_quarter}."
        )

    if tenancy_latest.empty:
        raise ValueError(
            f"No tenancy records found for {latest_quarter}."
        )

    airbnb_counts = (
        airbnb_latest
        .groupby(
            [
                "area_code",
                "area_name",
            ]
        )["id"]
        .nunique()
        .reset_index(
            name="airbnb_listings"
        )
    )

    comparison = airbnb_counts.merge(
        tenancy_latest,
        on="area_code",
        how="inner",
        validate="one_to_one",
    )

    if comparison.empty:
        raise ValueError(
            "No matching areas found for the Q3 comparison."
        )

    comparison = (
        comparison
        .sort_values(
            "airbnb_listings",
            ascending=False,
        )
        .head(TOP_COUNT_AREAS)
        .copy()
    )

    print(
        f"\nQ3: comparison for the "
        f"{latest_quarter} quarter, "
        f"top {TOP_COUNT_AREAS} areas by Airbnb count:"
    )

    print(
        comparison[
            [
                "area_name",
                "airbnb_listings",
                "Active Bonds",
                "Total Bonds",
            ]
        ].to_string(index=False)
    )

    # Plot Airbnb listings and active rental bonds side by side.
    fig, ax = plt.subplots(
        figsize=(11, 6)
    )

    x = range(
        len(comparison)
    )

    width = 0.35

    ax.bar(
        [
            i - width / 2
            for i in x
        ],
        comparison["airbnb_listings"],
        width,
        label="Airbnb listings",
    )

    ax.bar(
        [
            i + width / 2
            for i in x
        ],
        comparison["Active Bonds"],
        width,
        label="Active rental bonds",
    )

    ax.set_xticks(
        list(x)
    )

    ax.set_xticklabels(
        comparison["area_name"],
        rotation=45,
        ha="right",
    )

    ax.set_ylabel(
        "Count"
    )

    ax.set_title(
        "Airbnb listings vs. active rental bonds "
        f"by area ({latest_quarter})"
    )

    ax.legend()

    fig.tight_layout()

    fig.savefig(
        OUT_DIR / "q3_airbnb_vs_bonds_counts.png",
        dpi=150,
    )

    plt.close(fig)

    return comparison


# ---------------------------------------------------------------------------
# Main analysis pipeline
# ---------------------------------------------------------------------------

def main():
    """
    Load the prepared datasets, identify comparable periods, run the three
    analysis questions, and save the updated plots.
    """
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    listings = load_listings()

    tenancy = load_tenancy_overall()

    common_quarters = get_common_quarters(
        listings,
        tenancy,
    )

    q1_median_price_cc_central(
        listings
    )

    q2_price_gap(
        listings,
        tenancy,
        common_quarters,
    )

    q3_counts_comparison(
        listings,
        tenancy,
        common_quarters,
    )

    print(
        f"\nAnalysis complete. "
        f"Plots saved to {OUT_DIR}/"
    )


if __name__ == "__main__":
    main()