"""
Analyse the cleaned Christchurch Airbnb and Tenancy Services datasets after
Airbnb listings have been enriched with Stats NZ SA2 area codes.

Inputs:
    - listings_data/listings_christchurch_with_area.csv
      Cleaned Airbnb listings containing SA2 area codes and area names.
    - tenancy_data/tenancy_cleaned.csv
      Cleaned Tenancy Services rental bond data.

Main steps:
    1. Load the Airbnb data and map each Airbnb month to the matching
       tenancy quarter.
    2. Load the tenancy data and keep the overall dwelling/beds records.
    3. Calculate the median Airbnb nightly price for Christchurch Central.
    4. Join Airbnb and tenancy data by SA2 area code and quarter.
    5. Compare weekly-equivalent Airbnb prices with weekly median rent.
    6. Compare Airbnb listing counts with active rental bond counts.

Outputs:
    - Printed answers for the three analysis questions.
    - q2_price_gap_top_areas.png
    - q2_price_gap_distribution.png
    - q3_airbnb_vs_bonds_counts.png
      saved in output_graphs/.

Run from the repository root:
    python analysis.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

LISTINGS_FILE = "listings_data/listings_christchurch_with_area.csv"
TENANCY_FILE = "tenancy_data/tenancy_cleaned.csv"
OUT_DIR = Path("output_graphs")
MIN_LISTINGS_PER_AREA = 5   # areas with fewer listings than this are excluded
                            # from the "biggest gap" ranking (too noisy)

# ============================================================
# DELIVERABLE 6 CHANGE 1: Remove a magic number
#
# PREVIOUS CODE:
#     cc = a[a["area_code"] == 326600]
#
# MODIFIED CODE:
#     CHCH_CENTRAL_AREA_CODE = 326600
#     cc = a[a["area_code"] == CHCH_CENTRAL_AREA_CODE]
#
# NOTES:
# Previously, the value 326600 appeared directly inside the Q1 function.
# Someone reading the function would need to know what that number means.
# Giving it a descriptive name makes the purpose of the value clear and
# places an important parameter near the top of the script.
# ============================================================
CHCH_CENTRAL_AREA_CODE = 326600


# month name -> which quarter-start date it belongs to, matching the
# tenancy dataset's three TimeFrame values (Oct 2025, Jan 2026, Apr 2026)
MONTH_TO_QUARTER = {
    10: "2025-10-01", 11: "2025-10-01", 12: "2025-10-01",
    1: "2026-01-01", 2: "2026-01-01", 3: "2026-01-01",
    4: "2026-04-01", 5: "2026-04-01", 6: "2026-04-01",
}


def load_listings():
    """Load the Airbnb dataset, validate its columns, and assign quarters."""

    a = pd.read_csv(LISTINGS_FILE)

    # ========================================================
    # DELIVERABLE 6 CHANGE 2: Validate Airbnb input columns
    #
    # PREVIOUS CODE:
    #     a = pd.read_csv(LISTINGS_FILE)
    #     a["quarter_start"] = a["month"].map(MONTH_TO_QUARTER)
    #
    # MODIFIED CODE:
    # We now check that the columns required by the later analysis
    # actually exist before continuing.
    #
    # NOTES:
    # Previously, the script assumed that all required columns were
    # present. If a column was renamed or missing, the script would
    # fail later in the pipeline. The validation check detects the
    # problem immediately and gives a clearer error message.
    # ========================================================
    required_columns = {"id", "price", "month", "area_code", "area_name"}
    missing_columns = required_columns - set(a.columns)

    if missing_columns:
        raise ValueError(
            f"Airbnb data is missing required columns: {sorted(missing_columns)}"
        )

    a["quarter_start"] = a["month"].map(MONTH_TO_QUARTER)

    if a["quarter_start"].isna().any():
        bad = sorted(a.loc[a["quarter_start"].isna(), "month"].unique())
        raise ValueError(f"Months {bad} aren't in MONTH_TO_QUARTER — add them.")

    return a


def load_tenancy_overall():
    """
    Load the cleaned tenancy data and return one overall record for each
    SA2 area and quarter using Dwelling Type=ALL and Number Of Beds=ALL.
    """

    t = pd.read_csv(TENANCY_FILE)

    # ========================================================
    # DELIVERABLE 6 CHANGE 3: Validate tenancy input columns
    #
    # PREVIOUS CODE:
    #     t = pd.read_csv(TENANCY_FILE)
    #     t = t[t["Location Id"].notna() &
    #           (t["Location Id"] != -99)].copy()
    #
    # MODIFIED CODE:
    # Required columns are checked before filtering or analysis.
    #
    # NOTES:
    # Like the Airbnb data, the old code assumed that the tenancy
    # dataset had the expected structure. Checking the required
    # columns first makes the expected input explicit and makes
    # errors easier to identify.
    # ========================================================
    required_columns = {
        "Location Id",
        "Dwelling Type",
        "Number Of Beds",
        "TimeFrame",
        "Median Rent",
        "Total Bonds",
        "Active Bonds",
        "Closed Bonds"
    }

    missing_columns = required_columns - set(t.columns)

    if missing_columns:
        raise ValueError(
            f"Tenancy data is missing required columns: {sorted(missing_columns)}"
        )

    t = t[t["Location Id"].notna() & (t["Location Id"] != -99)].copy()
    t["area_code"] = t["Location Id"].astype(int)

    overall = t[
        (t["Dwelling Type"] == "ALL")
        & (t["Number Of Beds"] == "ALL")
    ].copy()

    overall = overall.rename(columns={"TimeFrame": "quarter_start"})

    return overall[
        [
            "area_code",
            "quarter_start",
            "Median Rent",
            "Total Bonds",
            "Active Bonds",
            "Closed Bonds"
        ]
    ]


def q1_median_price_cc_central(a):
    """Calculate the median nightly Airbnb price in Christchurch Central."""

    # Uses the named parameter added for Deliverable 6.
    cc = a[a["area_code"] == CHCH_CENTRAL_AREA_CODE]

    median_price = cc["price"].median()

    print(
        f"\nQ1: Median Airbnb price in Christchurch Central "
        f"({CHCH_CENTRAL_AREA_CODE}, n={len(cc)} "
        f"listing-months): ${median_price:.2f}/night"
    )

    return median_price


def q2_price_gap(a, tenancy_overall):
    """
    Join Airbnb and tenancy data by area and quarter, convert Airbnb nightly
    prices to a weekly equivalent, and calculate the median price gap by area.
    """

    merged = a.merge(
        tenancy_overall,
        on=["area_code", "quarter_start"],
        how="inner"
    )

    # ========================================================
    # DELIVERABLE 6 CHANGE 4: Sanity check the dataset join
    #
    # PREVIOUS CODE:
    #     merged = a.merge(...)
    #     merged["weekly_equiv_price"] = merged["price"] * 7
    #
    # MODIFIED CODE:
    #     merged = a.merge(...)
    #     if merged.empty:
    #         raise ValueError(...)
    #
    # NOTES:
    # This is our main sanity-check example. The analysis depends on
    # Airbnb and tenancy records matching by area code and quarter.
    # Previously, the script immediately continued after the join.
    # Now it confirms that the join produced records. If there are
    # no matches, the pipeline stops rather than producing misleading
    # or empty analysis results.
    # ========================================================
    if merged.empty:
        raise ValueError(
            "Sanity check failed: no Airbnb and tenancy records matched "
            "by area code and quarter."
        )

    merged["weekly_equiv_price"] = merged["price"] * 7
    merged["gap"] = merged["weekly_equiv_price"] - merged["Median Rent"]

    counts = merged.groupby("area_code")["id"].nunique()
    valid_areas = counts[counts >= MIN_LISTINGS_PER_AREA].index
    valid = merged[merged["area_code"].isin(valid_areas)]

    by_area = (
        valid.groupby(["area_code", "area_name"])["gap"]
        .median()
        .reset_index()
        .sort_values("gap", ascending=False)
    )

    print(
        f"\nQ2: {len(by_area)} areas with >= {MIN_LISTINGS_PER_AREA} matched "
        f"listing-months (of {merged['area_code'].nunique()} matched areas total)"
    )

    print("Top 5 largest gap (short-term price >> long-term rent):")
    print(by_area.head(5).to_string(index=False))

    print("Top 5 smallest / most negative gap:")
    print(by_area.tail(5).to_string(index=False))

    top15 = by_area.head(15)

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top15["area_name"], top15["gap"], color="#2b6cb0")
    ax.set_xlabel(
        "Median (short-term weekly-equivalent $ − long-term weekly rent $)"
    )
    ax.set_title(
        "Areas with the largest short-term vs long-term rental price gap"
    )
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "q2_price_gap_top_areas.png", dpi=150)
    plt.close(fig)

    top8_names = by_area.head(8)["area_code"]

    fig, ax = plt.subplots(figsize=(10, 6))

    plot_data = [
        valid.loc[valid["area_code"] == c, "gap"].dropna()
        for c in top8_names
    ]

    labels = [
        by_area.loc[
            by_area["area_code"] == c,
            "area_name"
        ].iloc[0]
        for c in top8_names
    ]

    ax.boxplot(plot_data, tick_labels=labels, vert=False)
    ax.set_xlabel("Weekly-equivalent short-term $ − long-term rent $")
    ax.set_title("Distribution of the price gap, top 8 areas by median gap")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "q2_price_gap_distribution.png", dpi=150)
    plt.close(fig)

    return by_area


def q3_counts_comparison(a, tenancy_overall):
    """
    Compare the number of unique Airbnb listings with active rental bonds
    for each area using the latest tenancy quarter.
    """

    airbnb_counts = (
        a.groupby(["area_code", "area_name"])["id"]
        .nunique()
        .reset_index(name="airbnb_listings")
    )

    # each area appears up to 3x in tenancy (one per quarter); use latest quarter
    latest_q = tenancy_overall["quarter_start"].max()

    bonds_latest = tenancy_overall[
        tenancy_overall["quarter_start"] == latest_q
    ]

    comp = airbnb_counts.merge(
        bonds_latest,
        on="area_code",
        how="inner"
    )

    comp = comp.sort_values(
        "airbnb_listings",
        ascending=False
    ).head(15)

    print(
        f"\nQ3: comparison for the {latest_q} quarter, "
        "top 15 areas by Airbnb count:"
    )

    print(
        comp[
            [
                "area_name",
                "airbnb_listings",
                "Active Bonds",
                "Total Bonds"
            ]
        ].to_string(index=False)
    )

    fig, ax = plt.subplots(figsize=(11, 6))

    x = range(len(comp))
    width = 0.35

    ax.bar(
        [i - width / 2 for i in x],
        comp["airbnb_listings"],
        width,
        label="Airbnb listings"
    )

    ax.bar(
        [i + width / 2 for i in x],
        comp["Active Bonds"],
        width,
        label="Active rental bonds"
    )

    ax.set_xticks(list(x))
    ax.set_xticklabels(
        comp["area_name"],
        rotation=45,
        ha="right"
    )

    ax.set_ylabel("Count")

    ax.set_title(
        f"Airbnb listings vs. active rental bonds by area ({latest_q})"
    )

    ax.legend()
    fig.tight_layout()

    fig.savefig(
        OUT_DIR / "q3_airbnb_vs_bonds_counts.png",
        dpi=150
    )

    plt.close(fig)

    return comp


def main():
    """Run all three analysis questions and save their graphs."""

    OUT_DIR.mkdir(exist_ok=True)

    a = load_listings()
    tenancy_overall = load_tenancy_overall()

    q1_median_price_cc_central(a)
    q2_price_gap(a, tenancy_overall)
    q3_counts_comparison(a, tenancy_overall)

    print(f"\nPlots saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()