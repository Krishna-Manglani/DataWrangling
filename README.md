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
| `availability_30` | Available days in the ne  xt 30 days. |
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



-----------------------------------------------------------------------------------------------

# Deliverable 4 — Data Cleaning

## Christchurch Airbnb Dataset

The Christchurch Airbnb dataset created in Deliverable 3 was cleaned to improve data quality and prepare it for later analysis and comparison with the Tenancy Services dataset.

**Original dataset:** 28,795 rows × 21 columns  
**Cleaned dataset:** 28,795 rows × 19 columns

### Cleaning Decisions

| Change | Reason | Consequence |
|---|---|---|
| Removed `license` | All values were missing, so the column contained no usable information. | 1 column removed |
| Removed `neighbourhood_group` | All records contained `Christchurch City`, making the column redundant after filtering to Christchurch. | 1 column removed |
| Retained `latitude` and `longitude` | Required for later geographic analysis. | Both columns retained |
| Retained `year`, `month`, and `month_year` | Required to identify the monthly Airbnb snapshots and match time periods with the Tenancy dataset. | All time columns retained |
| Standardised text fields | Leading and trailing spaces were removed to improve consistency. | No rows removed |
| Converted `last_review` to date format | Ensures review dates use a consistent format for later analysis. | No rows removed |
| Checked exact duplicates | Identical records would provide no additional information. | 0 duplicates found |
| Checked listing-month duplicates | A listing may appear across different months, but should not normally appear more than once within the same month. | 0 duplicate `id`, `year`, `month` combinations found |
| Retained legitimate missing values | Removing all incomplete records could cause unnecessary data loss. | No rows removed |
| Checked `price` | Prices were checked for zero, negative, and unusually high values. | 0 invalid prices; 153 prices above $1,000 identified and retained |
| Checked `availability_365` | Values should be between 0 and 365 days. | 0 invalid values |
| Checked `minimum_nights` | Non-missing values should be greater than zero. | 0 invalid values |

---

### Missing Values

Missing values were reviewed individually rather than automatically removed or imputed.

| Column | Missing Values | Decision |
|---|---:|---|
| `price` | 10,667 | Retained |
| `reviews_per_month` | 2,627 | Retained |
| `last_review` | 2,627 | Retained |
| `minimum_nights` | 37 | Retained |
| `host_name` | 1 | Retained |

Missing values were not automatically imputed because there was insufficient information to accurately replace them. Removing every incomplete row could also remove valid Airbnb listings.

---

### Outlier Checking

The `price` column was checked for unusually high values.

**153 observations had prices above NZD $1,000.**

These observations were retained rather than automatically removed because a high Airbnb price does not necessarily indicate an error and may represent a genuine listing.

---

### Cleaning Summary

| Measure | Before | After |
|---|---:|---:|
| Rows | 28,795 | 28,795 |
| Columns | 21 | 19 |
| Exact duplicates | 0 | 0 |

**Columns removed:**
- `license`
- `neighbourhood_group`

**Rows removed:** 0

The cleaning process intentionally preserved valid observations while removing redundant or unusable columns.

---

### Output Files

| File | Purpose |
|---|---|
| `clean_listing.py` | Reproducible Python cleaning pipeline |
| `listings_christchurch_cleaned.csv` | Cleaned Christchurch Airbnb dataset |
| `listings_cleaning_log.csv` | Record of cleaning decisions, reasons, and consequences |

The cleaned dataset and cleaning log are saved locally in the `listings_data` directory.



-----------------------------------------------------------------------------------------------




## Tenancy Services Rental Bond Dataset

### Dataset Source

This project uses the **Detailed Quarterly Rental Bond Data** published by **Tenancy Services / Ministry of Business, Innovation and Employment (MBIE)**.

- **Source:** Tenancy Services, Ministry of Business, Innovation and Employment
- **Dataset:** Detailed quarterly rental bond report
- **File used:** `Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv`
- **Geographic coverage:** New Zealand
- **Sector:** Private-sector rental properties
- **Frequency:** Quarterly

The data comes from the Tenancy Services tenancy bond database, which records new rental bonds lodged with Tenancy Services.

The data is organised using the **tenancy start date** and uses the **SA2-2019 geographic area definitions from Statistics New Zealand**.

### Dataset Columns

The dataset contains 12 columns:

| Column | Meaning |
|---|---|
| `TimeFrame` | The quarterly time period associated with the rental bond information. The source data is organised according to tenancy start date. |
| `Location Id` | Identifier for the geographic location represented by the record. The dataset uses Statistics New Zealand SA2-2019 geographic area definitions. |
| `Dwelling Type` | Type of rental dwelling represented by the record, such as house, flat, apartment, room, or boarding house. `ALL` represents all dwelling types combined. |
| `Number Of Beds` | Bedroom category for the rental property. The dataset includes individual bedroom categories as well as grouped values such as `5+` and `ALL`. |
| `Total Bonds` | Total number of rental bonds represented for the particular combination of time period, location, dwelling type, and bedroom category. |
| `Active Bonds` | Number of rental bonds classified as active for the record. |
| `Closed Bonds` | Number of rental bonds classified as closed for the record. |
| `Median Rent` | Median weekly rent. This is the middle weekly rent when observed rents are arranged from lowest to highest. |
| `Geometric Mean Rent` | Geometric mean of weekly rents. Tenancy Services provides this as an alternative measure to the median because rents tend to cluster around round numbers. For approximately log-normal rent data, the geometric mean closely approximates the median. |
| `Upper Quartile Rent` | Upper quartile weekly rent, representing the upper part of the rent distribution. Tenancy Services also uses a synthetic-quartile approach based on an assumed log-normal distribution. |
| `Lower Quartile Rent` | Lower quartile weekly rent, representing the lower part of the rent distribution. Tenancy Services also uses a synthetic-quartile approach based on an assumed log-normal distribution. |
| `Log Std Dev Weekly Rent` | Standard deviation of weekly rent values on the logarithmic scale. It describes the amount of variation in rents after the rent values are transformed to the log scale. |

### Rent Measures

Weekly rents often cluster around round values such as $300 or $400. Because of this, ordinary medians and quartiles can remain unchanged for several periods and then change suddenly.

Tenancy Services therefore provides additional rent measures:

- **Geometric Mean Rent:** an alternative summary measure that can closely approximate the median when rents follow an approximately log-normal distribution.
- **Synthetic Quartiles:** estimates of the 25th and 75th percentiles based on a log-normal distribution. These provide alternative measures for the lower and upper parts of the rent distribution.

### Privacy Protection

Tenancy Services applies privacy protection measures to the published rental bond data.

These include:

- **fixed random rounding to base 3**, and
- **suppression of results where fewer than 5 bonds are present for a particular selection**.

Because of these privacy measures, some counts may be rounded and some values may be missing or suppressed.

### Data Limitations

The rental bond data is currently considered **provisional** because Tenancy Services is migrating information from legacy systems to a new bond management system.

As a result:

- some figures may be incomplete or revised,
- reported changes may partly reflect system changes or data reclassification,
- methodology changes may affect reported values, and
- recent periods may not be directly comparable with earlier periods.

The latest available file should therefore be used when carrying out analysis.

### Licence and Attribution

The rental bond data is made available under the **Creative Commons Attribution 3.0 New Zealand licence**.

The data may be used free of charge for analysis provided that the source is credited as:

**The Ministry of Business, Innovation and Employment (MBIE).**

---------------------------------------------------------------------------------------

## Tenancy Services Dataset Cleaning

### Timeframe Filtering

The original Tenancy Services dataset contained **226,080 rows and 12 columns** and covered a wider period than the Christchurch Airbnb dataset.

To match the Airbnb data period from **October 2025 to June 2026**, the Tenancy dataset was filtered to the following quarterly periods:

- `2025-10-01` — Q4 2025
- `2026-01-01` — Q1 2026
- `2026-04-01` — Q2 2026

After filtering, **27,212 rows** remained.

### Cleaning Decisions

| Change | Reason | Consequence |
|---|---|---|
| Filtered `TimeFrame` | To match the October 2025 to June 2026 period of the Airbnb dataset. | 226,080 rows reduced to 27,212 rows. |
| Retained all 12 columns | All columns contain potentially useful rental bond information. | 0 columns removed. |
| Retained `Location Id` | Required for later geographic analysis and dataset matching. | Column retained. |
| Retained `TimeFrame` | Required for matching the Tenancy and Airbnb datasets by time period. | Column retained. |
| Standardised text fields | Removed leading and trailing spaces from categorical fields. | 0 rows removed. |
| Checked exact duplicates | Completely identical records would add no new information. | Exact duplicates were checked during cleaning. |
| Retained missing values | Some missing values may represent suppressed or unavailable information and should not be automatically deleted. | No rows removed because of missing values. |
| Checked bond counts | Negative bond counts would be invalid. | Bond count fields were validated. |
| Checked rent values | Zero or negative rent values would be invalid. | Rent fields were validated. |
| Checked rent quartile ordering | Lower quartile, median and upper quartile rent should follow a logical order. | Records were checked for inconsistent rent ordering. |

### Missing Values

The following missing values remained after cleaning:

| Column | Missing Values |
|---|---:|
| `Number Of Beds` | 890 |
| `Location Id` | 94 |
| `Median Rent` | 94 |
| `Geometric Mean Rent` | 94 |
| `Upper Quartile Rent` | 94 |
| `Lower Quartile Rent` | 94 |
| `Log Std Dev Weekly Rent` | 94 |

These values were retained because automatically removing all incomplete records could result in unnecessary data loss.

### Median Rent Summary

| Measure | Value |
|---|---:|
| Count | 27,118 |
| Mean | 617.33 |
| Median | 608.00 |
| Minimum | 90.00 |
| Maximum | 3,350.00 |

### Cleaning Result

| Measure | Before Cleaning | After Cleaning |
|---|---:|---:|
| Rows | 226,080 | 27,212 |
| Columns | 12 | 12 |

The cleaned dataset was saved locally as:

`tenancy_cleaned.csv`

The cleaning decisions and their consequences were also recorded in:

`tenancy_cleaning_log.csv`

The cleaning process can be reproduced using:

`clean_tenancy.py`