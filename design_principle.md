# Data Pipeline Design Principles

## Purpose and scope

This project prepares monthly Christchurch Airbnb listing data and quarterly Tenancy Services rental bond data, enriches Airbnb listings with Stats NZ SA2 geography, and compares short-term listing prices and counts with long-term rent and bond counts. The scripts are separate stages rather than one orchestrated command: run them from the repository root in the order described below. The Airbnb source CSVs and the Koordinates API key are external inputs; the API key must be set in the `KOORDINATES_KEY` environment variable before running `get_area_codes.py`.

## Inputs and outputs

### Airbnb

`process_listings.py` reads `listings_data/listings_*.csv` (the monthly snapshots from October 2025 through June 2026). It filters rows to Christchurch, adds `year`, `month`, and `month_year`, and writes:

- `listings_data/listings_christchurch_oct25_jun26.csv`
- `listings_data/listings_christchurch_summary.csv`

`clean_listing.py` reads the combined CSV and writes `listings_data/listings_christchurch_cleaned.csv` and `listings_data/listings_cleaning_log.csv`. It retains 19 selected source columns, removes `license` and `neighbourhood_group`, standardises selected text and date fields, records missing values and validation results, and flags prices above $1,000 with `price_review_flag` instead of deleting them.

`get_area_codes.py` reads the cleaned listings and writes `listings_data/listings_christchurch_with_area.csv`, adding `area_code` and `area_name`. It also reads and writes `listings_data/area_code_cache.csv` so completed coordinate lookups can be reused. A completed lookup with no SA2 feature is cached with missing area fields; failed requests are not treated as completed and can be retried on a later run.

### Tenancy Services

`clean_tenancy.py` reads `tenancy_data/Detailed-Quarterly-Tenancy-Q1-2020-Q3-2026.csv` and writes `tenancy_data/tenancy_cleaned.csv` and `tenancy_data/tenancy_cleaning_log.csv`. It retains the 12 source columns and filters to 1 October 2025, 1 January 2026, and 1 April 2026, the three quarters covering the Airbnb study period.

### Analysis and plots

`analysis.py` reads the enriched Airbnb CSV and cleaned tenancy CSV. It prints the Christchurch Central median Airbnb nightly price, calculates the area price gap, and compares unique Airbnb listings with bond counts for the latest tenancy quarter. It writes three figures to `output_graphs/`: `q2_price_gap_top_areas.png`, `q2_price_gap_distribution.png`, and `q3_airbnb_vs_bonds_counts.png`.

`Deliverable3plots.py` is a separate exploratory plotting script. It reads the combined, pre-cleaning Christchurch Airbnb CSV and writes a price distribution plot plus monthly days-since-review plots under `output_graphs/`. It also prints the top 10% of listings by review count. These plots are not outputs of `analysis.py`.

## Pipeline steps

1. **Combine and filter Airbnb snapshots.** `process_listings.py` accepts monthly source filenames such as `listings_Oct25.csv`, chooses an available Christchurch-location column, filters to Christchurch, derives the month and year from each filename, concatenates the monthly rows, and produces a per-column summary. It warns if source files have different column counts, but still concatenates them. Its filename filter excludes generated datasets, so rerunning it does not treat its previous output as a new monthly source file.
2. **Clean both sources independently.** `clean_listing.py` selects and validates Airbnb fields, preserves rows with legitimate missing values, and records decisions in a cleaning log. `clean_tenancy.py` selects the matching quarters, standardises fields, validates numeric and rent-ordering rules, and records its decisions in a separate log.
3. **Enrich Airbnb geography.** `get_area_codes.py` rounds coordinates to six decimal places, looks up unique coordinate pairs through the Koordinates Query API, caches completed results, and joins area codes and names back to listing rows. It prints the successful SA2 match rate.
4. **Compare by area and quarter.** `analysis.py` maps October–December 2025 to the 1 October quarter, January–March 2026 to 1 January, and April–June 2026 to 1 April. For the price-gap analysis it filters tenancy rows to `Dwelling Type=ALL` and `Number Of Beds=ALL`, inner-joins on SA2 area code and quarter, multiplies Airbnb nightly prices by seven, and compares that weekly equivalent with `Median Rent`. Areas with fewer than five unique matched Airbnb listing IDs are excluded from the ranking. For the count comparison, unique Airbnb listing IDs across the available Airbnb months are compared with active and total bonds in the latest tenancy quarter.

## Design and coding practices

### Modular scripts and functions

Combining, cleaning, geographic enrichment, analysis, and exploratory plotting are kept in separate scripts. The cleaning and analysis scripts also split work into named functions. This keeps each stage understandable and makes its inputs and outputs easier to identify.

### File paths and run location

Paths are relative to the process's current working directory, not calculated from the script's location. Run the scripts from the repository root so paths such as `listings_data/...` and `tenancy_data/...` resolve as intended. This avoids machine-specific absolute paths, but the run location is part of the setup requirement.

### Named parameters and explicit rules

Analysis values with meaning are named near the top of the script, including `CHCH_CENTRAL_AREA_CODE` and `MIN_LISTINGS_PER_AREA`. The quarter mapping and the coordinate lookup settings are also defined explicitly. This makes key assumptions easier to find and revise.

### Input validation and sanity checks

The cleaning scripts check expected input columns and apply validation and final sanity checks. `analysis.py` checks required columns and rejects unexpected Airbnb months; it also stops if the area-and-quarter join is empty. `get_area_codes.py` checks for latitude and longitude before querying and reports the proportion of listing rows with an SA2 area code. These checks make several input and processing problems visible early, though the match-rate report is informational rather than a pass/fail threshold.

### API key handling and caching

The Koordinates key is read from the `KOORDINATES_KEY` environment variable and is not embedded in the source. The coordinate cache avoids repeating completed lookups, including completed lookups that returned no area feature. Request failures are omitted from the cache so a rerun can try them again.

### Logs and documentation

The cleaning scripts save CSV logs with cleaning decisions, reasons, and impacts. Docstrings and comments describe script behavior; some comments are presentation notes explaining code-review changes. The design principles document describes implemented behavior and the assumptions those scripts use.

## Alignment review

The implementation and this document were compared script by script. This review corrected descriptions that did not match the code: file paths are resolved from the current working directory (so the repository root is the expected run location), and the area lookup cache includes completed no-feature results as well as successful matches. It also found that `process_listings.py` originally selected every `listings_*.csv`, including its own generated outputs on later runs. The input selection now accepts monthly snapshot filenames only. The exploratory plots from `Deliverable3plots.py` are distinguished from the three analysis plots. The intended geographic and time-period comparisons are reflected in the analysis description above.

## AI use

ChatGPT (OpenAI) assisted with reviewing the code against the design principles and drafting this document. The project code and analysis assumptions were used to check the final descriptions.
