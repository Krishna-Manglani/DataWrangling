"""
Combine the cleaned Christchurch Airbnb data (with SA2 area codes) and the
cleaned Tenancy Services bond data, then answer:

  1. Median Airbnb price in Christchurch Central (area code 326600)
  2. Where is the gap between short-term and long-term rental prices biggest?
  3. How do Airbnb listing counts compare to rental bond counts, by area?

Run from the repo root:
    python analysis.py
Plots are saved to output_graphs/, nothing is shown interactively so it also
works headlessly (e.g. in CI or over SSH).
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

# month name -> which quarter-start date it belongs to, matching the
# tenancy dataset's three TimeFrame values (Oct 2025, Jan 2026, Apr 2026)
MONTH_TO_QUARTER = {
    10: "2025-10-01", 11: "2025-10-01", 12: "2025-10-01",
    1: "2026-01-01", 2: "2026-01-01", 3: "2026-01-01",
    4: "2026-04-01", 5: "2026-04-01", 6: "2026-04-01",
}


def load_listings():
    a = pd.read_csv(LISTINGS_FILE)
    a["quarter_start"] = a["month"].map(MONTH_TO_QUARTER)
    if a["quarter_start"].isna().any():
        bad = sorted(a.loc[a["quarter_start"].isna(), "month"].unique())
        raise ValueError(f"Months {bad} aren't in MONTH_TO_QUARTER — add them.")
    return a


def load_tenancy_overall():
    """One row per (area, quarter): the Dwelling Type=ALL / Beds=ALL summary."""
    t = pd.read_csv(TENANCY_FILE)
    t = t[t["Location Id"].notna() & (t["Location Id"] != -99)].copy()
    t["area_code"] = t["Location Id"].astype(int)
    overall = t[(t["Dwelling Type"] == "ALL") & (t["Number Of Beds"] == "ALL")].copy()
    overall = overall.rename(columns={"TimeFrame": "quarter_start"})
    return overall[["area_code", "quarter_start", "Median Rent",
                     "Total Bonds", "Active Bonds", "Closed Bonds"]]


def q1_median_price_cc_central(a):
    cc = a[a["area_code"] == 326600]
    median_price = cc["price"].median()
    print(f"\nQ1: Median Airbnb price in Christchurch Central (326600, n={len(cc)} "
          f"listing-months): ${median_price:.2f}/night")
    return median_price


def q2_price_gap(a, tenancy_overall):
    merged = a.merge(tenancy_overall, on=["area_code", "quarter_start"], how="inner")
    merged["weekly_equiv_price"] = merged["price"] * 7
    merged["gap"] = merged["weekly_equiv_price"] - merged["Median Rent"]

    counts = merged.groupby("area_code")["id"].nunique()
    valid_areas = counts[counts >= MIN_LISTINGS_PER_AREA].index
    valid = merged[merged["area_code"].isin(valid_areas)]

    by_area = (valid.groupby(["area_code", "area_name"])["gap"]
               .median().reset_index().sort_values("gap", ascending=False))

    print(f"\nQ2: {len(by_area)} areas with >= {MIN_LISTINGS_PER_AREA} matched "
          f"listing-months (of {merged['area_code'].nunique()} matched areas total)")
    print("Top 5 largest gap (short-term price >> long-term rent):")
    print(by_area.head(5).to_string(index=False))
    print("Top 5 smallest / most negative gap:")
    print(by_area.tail(5).to_string(index=False))

    top15 = by_area.head(15)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top15["area_name"], top15["gap"], color="#2b6cb0")
    ax.set_xlabel("Median (short-term weekly-equivalent $ − long-term weekly rent $)")
    ax.set_title("Areas with the largest short-term vs long-term rental price gap")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "q2_price_gap_top_areas.png", dpi=150)
    plt.close(fig)

    top8_names = by_area.head(8)["area_code"]
    fig, ax = plt.subplots(figsize=(10, 6))
    plot_data = [valid.loc[valid["area_code"] == c, "gap"].dropna() for c in top8_names]
    labels = [by_area.loc[by_area["area_code"] == c, "area_name"].iloc[0] for c in top8_names]
    ax.boxplot(plot_data, tick_labels=labels, vert=False)
    ax.set_xlabel("Weekly-equivalent short-term $ − long-term rent $")
    ax.set_title("Distribution of the price gap, top 8 areas by median gap")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "q2_price_gap_distribution.png", dpi=150)
    plt.close(fig)

    return by_area


def q3_counts_comparison(a, tenancy_overall):
    airbnb_counts = (a.groupby(["area_code", "area_name"])["id"]
                     .nunique().reset_index(name="airbnb_listings"))
    # each area appears up to 3x in tenancy (one per quarter); use latest quarter
    latest_q = tenancy_overall["quarter_start"].max()
    bonds_latest = tenancy_overall[tenancy_overall["quarter_start"] == latest_q]

    comp = airbnb_counts.merge(bonds_latest, on="area_code", how="inner")
    comp = comp.sort_values("airbnb_listings", ascending=False).head(15)

    print(f"\nQ3: comparison for the {latest_q} quarter, top 15 areas by Airbnb count:")
    print(comp[["area_name", "airbnb_listings", "Active Bonds", "Total Bonds"]]
          .to_string(index=False))

    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(comp))
    width = 0.35
    ax.bar([i - width / 2 for i in x], comp["airbnb_listings"], width, label="Airbnb listings")
    ax.bar([i + width / 2 for i in x], comp["Active Bonds"], width, label="Active rental bonds")
    ax.set_xticks(list(x))
    ax.set_xticklabels(comp["area_name"], rotation=45, ha="right")
    ax.set_ylabel("Count")
    ax.set_title(f"Airbnb listings vs. active rental bonds by area ({latest_q})")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT_DIR / "q3_airbnb_vs_bonds_counts.png", dpi=150)
    plt.close(fig)

    return comp


def main():
    OUT_DIR.mkdir(exist_ok=True)
    a = load_listings()
    tenancy_overall = load_tenancy_overall()

    q1_median_price_cc_central(a)
    q2_price_gap(a, tenancy_overall)
    q3_counts_comparison(a, tenancy_overall)

    print(f"\nPlots saved to {OUT_DIR}/")


if __name__ == "__main__":
    main()
