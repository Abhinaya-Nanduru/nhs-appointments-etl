# NHS GP Appointments ETL Pipeline

## Project Overview

This project builds a repeatable ETL data pipeline using NHS England GP appointment data.

The aim of the project is to process and organise GP appointment data so that it can later be used to calculate KPIs and support decision-making about appointment demand, waiting times, missed appointments (DNAs), appointment modes and consultation duration.

The final pipeline will transform the NHS source files into a structured data warehouse that can support monthly KPI reporting.

## Data Source

The project uses public NHS England **Appointments in General Practice** data.

The three main datasets are:

* `appointments_regional.csv`
* `national_categories.csv`
* `actual_duration.csv.xlsx`

A metadata file is also provided to explain the source fields.

The actual NHS data files are not stored in this GitHub repository.

## Week 1 - Extract and Profile

The objective of Week 1 is to safely extract and understand the raw NHS data before transformation.

### Extraction

The `src/extract.py` script:

* Copies the original source files into the project's raw data layer.
* Preserves the original source files.
* Converts the actual-duration Excel file into CSV format.
* Calculates SHA-256 checksums.
* Records file sizes and row counts.
* Creates a `manifest.json` file for traceability.

Expected source row counts:

| Dataset                   |    Rows |
| ------------------------- | ------: |
| appointments_regional.csv | 596,821 |
| national_categories.csv   | 817,394 |
| actual_duration.csv.xlsx  | 137,793 |

### Data Profiling

The three datasets were profiled to understand:

* Row and column counts
* Column names
* Data types
* Null values
* Distinct values
* Date ranges
* Dataset grain

The profiling results are documented in:

`docs/data_profile.md`

## Data Quality Issues

Five important data issues were identified during profiling:

1. The actual-duration source file is an Excel file despite its unusual `.csv.xlsx` filename.
2. The national categories data can contain a hidden byte-order mark (BOM).
3. Dates require careful day-first parsing.
4. Duplicate-looking regional rows must not simply be removed.
5. Some categorical labels contain inconsistent spelling or spacing.

These issues are documented in:

`docs/data_quality_notes.md`

They will be handled during the transformation stage.

## Project Structure

```text
NHS_ETL_Project/
├── data/
│   ├── raw/
│   └── clean/
├── src/
│   └── extract.py
├── tests/
├── docs/
│   ├── data_profile.md
│   └── data_quality_notes.md
├── README.md
└── .gitignore
```

## Pipeline

The project follows an ETL approach:

**Extract → Transform → Load**

* **Extract:** Collect and preserve the NHS source data.
* **Transform:** Clean, standardise and validate the datasets.
* **Load:** Load the transformed data into a structured data warehouse for KPI reporting.

## Week 1 Status

* GitHub repository and project structure created
* Raw data extraction completed
* Excel duration data converted to CSV
* Manifest and SHA-256 checksums created
* Expected row counts verified
* Data profiling completed
* Dataset grains documented
* Five known data-quality issues documented

## Next Stage

Week 2 will focus on transforming and cleaning the raw data and producing tested Parquet files.
