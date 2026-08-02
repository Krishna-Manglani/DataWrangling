# Airbnb Listings Dataset

## Dataset Source

This project uses the **Inside Airbnb** dataset for **New Zealand (June 2026)**.

- **Source:** https://insideairbnb.com/get-the-data/
- **Dataset:** `listings.csv`
- **Geographic Coverage:** New Zealand
- **Snapshot Date:** June 2026

Inside Airbnb is an independent project that provides publicly available data collected from Airbnb listings. The data is intended for research, analysis, and public discussion about the short-term rental market.

---

# Dataset Description

The `listings.csv` dataset contains detailed information about Airbnb listings, including:

- Listing information
- Host information
- Property characteristics
- Location details
- Pricing
- Availability
- Reviews
- Booking policies
- Licensing information (where available)

Each row represents one Airbnb listing.

---

# Key Columns

| Column | Description |
|---------|-------------|
| `id` | Unique identifier for the listing. |
| `listing_url` | URL of the Airbnb listing. |
| `scrape_id` | Identifier of the data collection (scrape). |
| `last_scraped` | Date the listing information was collected. |
| `source` | Source of the listing data. |
| `name` | Name/title of the listing. |
| `description` | Listing description provided by the host. |
| `neighborhood_overview` | Host's description of the neighbourhood. |
| `picture_url` | Main image of the listing. |
| `host_id` | Unique identifier for the host. |
| `host_url` | URL of the host profile. |
| `host_name` | Host's first name. |
| `host_since` | Date the host joined Airbnb. |
| `host_location` | Location specified by the host. |
| `host_response_time` | Typical response time of the host. |
| `host_response_rate` | Percentage of enquiries responded to. |
| `host_acceptance_rate` | Percentage of booking requests accepted. |
| `host_is_superhost` | Whether the host is a Superhost. |
| `host_neighbourhood` | Host's neighbourhood. |
| `host_listings_count` | Number of listings owned by the host. |
| `host_total_listings_count` | Total listings managed by the host. |
| `host_identity_verified` | Whether Airbnb has verified the host's identity. |
| `neighbourhood` | General neighbourhood name. |
| `latitude` | Latitude coordinate. |
| `longitude` | Longitude coordinate. |
| `property_type` | Type of property (Apartment, House, etc.). |
| `room_type` | Entire home, private room, shared room, etc. |
| `accommodates` | Maximum number of guests. |
| `bathrooms_text` | Bathroom information. |
| `bedrooms` | Number of bedrooms. |
| `beds` | Number of beds. |
| `amenities` | List of amenities provided. |
| `price` | Nightly listing price. |
| `minimum_nights` | Minimum booking duration. |
| `maximum_nights` | Maximum booking duration. |
| `availability_30` | Available days in the next 30 days. |
| `availability_60` | Available days in the next 60 days. |
| `availability_90` | Available days in the next 90 days. |
| `availability_365` | Available days in the next year. |
| `number_of_reviews` | Total number of reviews received. |
| `number_of_reviews_ltm` | Reviews received in the last 12 months. |
| `review_scores_rating` | Overall guest rating. |
| `review_scores_accuracy` | Rating for listing accuracy. |
| `review_scores_cleanliness` | Cleanliness rating. |
| `review_scores_checkin` | Check-in rating. |
| `review_scores_communication` | Communication rating. |
| `review_scores_location` | Location rating. |
| `review_scores_value` | Value-for-money rating. |
| `instant_bookable` | Whether guests can book instantly. |
| `license` | Registration or licence information (if applicable). |


# Data Notes

- Missing values are present in several columns and may require preprocessing.
- Prices are stored as text with currency symbols and commas and should be converted to numeric values before analysis.
- Geographic coordinates can be used for mapping and spatial analysis.
- Review score columns generally range from 1 to 5.
- Availability columns indicate the number of days the property is available over different time horizons.
