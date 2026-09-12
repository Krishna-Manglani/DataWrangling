import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------------------------------------
# File locations
# -----------------------------------------------------------

DATA_FILE = Path(
    "listings_data/listings_christchurch_oct25_jun26.csv"
)

OUTPUT_DIR = Path("output_graphs")

# Create output_graphs automatically if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)


# -----------------------------------------------------------
# Load Christchurch data
# -----------------------------------------------------------

df = pd.read_csv(DATA_FILE)


# -----------------------------------------------------------
# 1. PRICE DISTRIBUTION
# KNIME equivalent:
# Row Filter -> Histogram
# -----------------------------------------------------------

price_data = df[
    (df["price"].notna()) &
    (df["price"] > 0) &
    (df["price"] <= 1000)
]

plt.figure()

plt.hist(
    price_data["price"],
    bins=30
)

plt.xlabel("Price (NZD)")
plt.ylabel("Number of Listings")
plt.title("Christchurch Airbnb Price Distribution")

plt.savefig(
    OUTPUT_DIR / "price_distribution.png",
    bbox_inches="tight"
)

plt.close()

print("Saved: output_graphs/price_distribution.png")


# -----------------------------------------------------------
# 2. DAYS SINCE LAST REVIEW
# KNIME equivalent:
# String to Date&Time
# -> Row Filter
# -> Date&Time Difference
# -> Histogram
#
# Each monthly dataset uses its own fixed reference date.
# -----------------------------------------------------------

review_data = df.copy()

# Convert last_review into proper dates
review_data["last_review"] = pd.to_datetime(
    review_data["last_review"],
    errors="coerce"
)

# Remove rows with missing last_review values
review_data = review_data.dropna(
    subset=["last_review"]
)

# Fixed reference date for each monthly dataset
reference_dates = {
    "Oct-2025": pd.Timestamp("2025-10-05"),
    "Nov-2025": pd.Timestamp("2025-11-07"),
    "Dec-2025": pd.Timestamp("2025-12-11"),
    "Jan-2026": pd.Timestamp("2026-01-16"),
    "Feb-2026": pd.Timestamp("2026-02-13"),
    "March-2026": pd.Timestamp("2026-03-17"),
    "April-2026": pd.Timestamp("2026-04-16"),
    "May-2026": pd.Timestamp("2026-05-23"),
    "June-2026": pd.Timestamp("2026-06-19")
}

# Match each row with the correct reference date
# using the month_year column
review_data["reference_date"] = review_data["month_year"].map(
    reference_dates
)

# Remove rows that do not have a matching reference date
review_data = review_data.dropna(
    subset=["reference_date"]
)

# Calculate the number of days between the monthly
# reference date and the last review
review_data["days_since_review"] = (
    review_data["reference_date"] -
    review_data["last_review"]
).dt.days


# -----------------------------------------------------------
# Create one review histogram for each month
# -----------------------------------------------------------

for month_year in reference_dates:

    month_data = review_data[
        review_data["month_year"] == month_year
    ]

    plt.figure()

    plt.hist(
        month_data["days_since_review"],
        bins=30
    )

    plt.xlabel("Days Since Last Review")
    plt.ylabel("Number of Listings")
    plt.title(
        f"Days Since Last Airbnb Review - {month_year}"
    )

    filename = (
        "days_since_review_"
        + month_year.lower().replace("-", "_")
        + ".png"
    )

    plt.savefig(
        OUTPUT_DIR / filename,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Saved: output_graphs/{filename}"
    )


# -----------------------------------------------------------
# 3. TOP 10% BY NUMBER OF REVIEWS
# KNIME equivalent:
# Sorter -> Top K Row Filter -> Table View
# -----------------------------------------------------------

sorted_reviews = df.sort_values(
    "number_of_reviews",
    ascending=False
)

top_10_count = int(
    len(sorted_reviews) * 0.10
)

top_10 = sorted_reviews.head(
    top_10_count
)

print(
    "\nTop 10% of listings by number of reviews:"
)

print(
    top_10[[
        "name",
        "number_of_reviews"
    ]]
)