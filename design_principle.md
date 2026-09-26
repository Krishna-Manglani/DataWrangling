# Data Pipeline Design Principles

## Purpose

The purpose of this pipeline is to prepare, clean, enrich, combine, and analyse Christchurch Airbnb and Tenancy Services data. The final analysis compares short-term Airbnb accommodation with long-term rental information across different areas in Christchurch.

## 1. Inputs to the Pipeline

The pipeline uses two main data sources.

### Airbnb Data

The Airbnb input consists of monthly listing CSV files from October 2025 to June 2026. These files contain information about Airbnb listings, including listing ID, price, location, latitude, longitude, reviews, availability, year, and month.

The monthly files are combined and filtered to Christchurch before being cleaned and used in later stages of the pipeline.

### Tenancy Services Data

The second input is the Tenancy Services rental bond dataset. It contains long-term rental information for different locations and time periods.

Important fields used by the pipeline include:

- Location Id
- TimeFrame
- Median Rent
- Dwelling Type
- Number Of Beds
- Total Bonds
- Active Bonds
- Closed Bonds

The tenancy data is cleaned and restricted to the quarters that correspond with the Airbnb data.

---

## 2. Outputs from the Pipeline

The pipeline produces intermediate and final outputs.

The main outputs are:

- A combined Christchurch Airbnb dataset.
- A cleaned Christchurch Airbnb dataset.
- A cleaned Tenancy Services dataset.
- An Airbnb dataset enriched with Stats NZ SA2 area codes and area names.
- A cache of completed coordinate and SA2 lookups.
- Analysis results comparing Airbnb and long-term rental data.
- Graphs saved in the `output_graphs` folder.

The final analysis answers three main questions:

1. What is the median Airbnb price in Christchurch Central?
2. Which areas have the largest gap between weekly-equivalent Airbnb prices and long-term median rent?
3. How do Airbnb listing counts compare with rental bond counts by area?

---

## 3. Main Steps in the Pipeline

### Step 1: Combine Airbnb Data

The monthly Airbnb files are combined into one dataset and filtered to Christchurch. Month and year information is retained so listings can be compared across the study period.

### Step 2: Clean the Airbnb Data

The Airbnb dataset is cleaned by keeping the fields required for the project and checking the quality of important variables. The cleaned dataset is saved for later processing.

### Step 3: Clean the Tenancy Data

The Tenancy Services dataset is cleaned separately. The required time periods are selected so that the tenancy data corresponds with the Airbnb study period.

### Step 4: Add SA2 Area Codes

`get_area_codes.py` uses the latitude and longitude of Airbnb listings to obtain Stats NZ SA2 area codes and area names through the Koordinates API.

Completed coordinate lookups are cached so that the same locations do not need to be requested again when the script is rerun.

### Step 5: Combine Airbnb and Tenancy Data

In `analysis.py`, Airbnb months are mapped to the corresponding tenancy quarters. The Airbnb and tenancy datasets are then matched using the SA2 area code and quarter.

### Step 6: Analyse the Data

The combined data is used to calculate and compare Airbnb and long-term rental information.

The analysis calculates:

- The median Airbnb nightly price in Christchurch Central.
- The difference between weekly-equivalent Airbnb prices and weekly median rent by area.
- Airbnb listing counts compared with active rental bond counts.

Graphs from the analysis are saved in the `output_graphs` folder.

---

## 4. Coding and Software Strategies

Several coding and software practices are used to make the pipeline easier to understand, maintain, and check.

### Modular Code

Different stages of the pipeline are separated into different Python scripts. For example, data processing, cleaning, geographic enrichment, and analysis are handled separately. Functions are also used within the scripts to separate individual tasks.

This makes the pipeline easier to understand and allows problems to be identified within a particular stage.

### Relative File Paths

The scripts use relative file paths based on the project directory instead of absolute paths that are specific to one computer.

This makes it easier for different team members to run the project without changing file paths for their own computers.

### Clear Parameters

Important values are given descriptive parameter names.

For example:

`CHCH_CENTRAL_AREA_CODE = 326600`

is used instead of placing `326600` directly inside the analysis function.

This avoids a magic number and makes the purpose of the value clearer.

### Input Validation

The pipeline checks that important columns are available before some processing steps are performed.

For example, `analysis.py` checks the required columns in the Airbnb and tenancy datasets. `get_area_codes.py` checks that latitude and longitude columns are available before geographic API requests are made.

This helps identify incorrect inputs earlier in the pipeline.

### Sanity Checking

Sanity checks are used to check important intermediate or output results before they are trusted.

In `analysis.py`, the pipeline checks whether the join between the Airbnb and tenancy datasets produced any records. If no records match by area code and quarter, the pipeline stops with an error instead of continuing with the price-gap analysis.

In `get_area_codes.py`, the pipeline also reports the percentage of Airbnb listings that successfully received an SA2 area code. This provides a simple check of whether the geographic enrichment worked as expected.

### API Key Management

The Koordinates API key is stored in the `KOORDINATES_KEY` environment variable instead of being written directly into the Python source code.

This keeps the API key separate from the code and reduces the risk of accidentally committing it to the repository.

### Caching API Results

Completed SA2 coordinate lookups are stored in `area_code_cache.csv`.

This allows the geographic enrichment process to be resumed without repeating successful API requests.

### Documentation

Docstrings and comments are used to describe the purpose of the scripts, their inputs and outputs, and important processing steps.

Comments were also added during the Week 9 code review to document the coding-practice changes and provide a guide for explaining the changes during the presentation.

---

## Design and Code Alignment Check

The Design Principles document was reviewed against the actual pipeline to make sure that the documented design matches the implementation.

The inputs, outputs, main pipeline steps, and coding strategies described above are reflected in the current project code.

During the Week 9 code review, some areas for improvement were identified. These included replacing a magic number with a named parameter, adding input validation, and adding sanity checks to important pipeline steps. These changes were added to the existing code without changing the main analysis process.

The updated code was also checked against the intended pipeline so that the documentation and implementation remain consistent.

---

## AI Use

AI tool used: **ChatGPT (OpenAI)**.

ChatGPT was used to assist with reviewing the existing pipeline against the coding practices discussed in the lectures and to help construct this Design Principles document.

The AI-generated suggestions were reviewed against the actual project code. The final content and coding decisions reflect the team's understanding of the pipeline and the decisions made during the project.