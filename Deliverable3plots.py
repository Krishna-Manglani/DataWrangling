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
# String to Date&Time -> Row Filter
# -> Date&Time Difference -> Histogram
# -----------------------------------------------------------

review_data = df.copy()

review_data["last_review"] = pd.to_datetime(
    review_data["last_review"],
    errors="coerce"
)

review_data = review_data.dropna(
    subset=["last_review"]
)

reference_date = pd.Timestamp("2026-06-30")

review_data["days_since_review"] = (
    reference_date - review_data["last_review"]
).dt.days


plt.figure()

plt.hist(
    review_data["days_since_review"],
    bins=30
)

plt.xlabel("Days Since Last Review")
plt.ylabel("Number of Listings")
plt.title("Days Since Last Airbnb Review")

plt.savefig(
    OUTPUT_DIR / "days_since_review.png",
    bbox_inches="tight"
)

plt.close()

print("Saved: output_graphs/days_since_review.png")


# -----------------------------------------------------------
# 3. TOP 10% BY NUMBER OF REVIEWS
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

print("\nTop 10% of listings by number of reviews:")

print(
    top_10[[
        "name",
        "number_of_reviews"
    ]]
)