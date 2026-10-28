# Week 2 Decision Log

## 1. Duration Source File

**Decision:** Read the actual-duration source using pandas as an Excel file.

**Reason:** The source is an Excel workbook despite its unusual `.csv.xlsx` filename.

**Action:** The Excel data is read with `pandas.read_excel()` before being converted to a Spark DataFrame.

---

## 2. Hidden BOM in Categories

**Decision:** Remove the hidden byte-order mark (BOM) from column names.

**Reason:** A BOM can cause the first column name to be interpreted incorrectly.

**Action:** Column names are checked and `\ufeff` is removed before transformation.

---

## 3. Day-First Dates

**Decision:** Parse category appointment dates explicitly using day-first format.

**Reason:** The source dates use `dd/MM/yyyy`. Allowing automatic date inference could interpret dates incorrectly.

**Action:** A cleaned appointment-date column is created while retaining the original source column.

---

## 4. Regional Look-Alike Rows

**Decision:** Aggregate look-alike regional rows by summing `count_of_appointments`. They are not dropped as duplicates.

**Reason:** The rows represent real appointments originating from different sub-ICB locations even though those locations are not represented in the regional file's grain.

**Result:** Regional data was reduced from 596,821 rows to 295,692 rows while preserving the total of 742,804,525 appointments.

---

## 5. Inconsistent Labels

**Decision:** Standardise categorical labels by trimming whitespace, collapsing repeated spaces and using one spelling of `Other Practice Staff`.

**Reason:** Equivalent labels must not be treated as separate categories because of formatting differences.

---

# KPI Denominator Decisions

Rates will be calculated at query time rather than stored in the clean data.

## DNA Rate

Denominator:

Attended + DNA

Rows with an Unknown appointment status are excluded.

## Same-Day Share

Denominator:

Appointments with a known booking-wait value.

Unknown booking-wait values are excluded.

## Long-Wait Share

Denominator:

Appointments with a known booking-wait value.

Unknown booking-wait values are excluded.

## Face-to-Face Share

Denominator:

Appointments with a known appointment mode.

Unknown appointment modes are excluded.

## GP Share

Denominator:

Appointments with a known staff type.

Unknown staff types are excluded.

The warehouse will store appointment counts rather than pre-calculated percentages so that rates can be calculated correctly for different aggregation levels.

---

# Partial-Year Decision

The regional dataset ends in June 2022.

Therefore, 2022 will not be compared as a full year against complete previous years.

Year-on-year analysis will compare equivalent periods, for example January-June 2022 with January-June 2021, or compare the same month with the same month in the previous year.

---

# Population Limitation

The supplied datasets do not contain registered-patient population counts.

Therefore, appointments per 1,000 patients cannot be calculated from these files. Raw appointment totals should not be used to imply fair comparisons between ICBs with different population sizes.

---

# Why Three Fact Tables?

The three NHS datasets have different grains.

Combining them into one large fact table would multiply rows during joins and could inflate appointment totals.

Therefore, the warehouse design uses three fact tables:

1. `fact_appointments_monthly`
2. `fact_appointments_by_category`
3. `fact_appointments_by_duration`

The fact tables will only be compared after aggregation to an appropriate shared level, such as month.

This preserves the original grain and prevents double counting.


---

# Week 3 - Load and Automation Decisions

## 1. DuckDB as the analytical warehouse

DuckDB was selected as the local analytical warehouse because it can query
Parquet files directly and provides a lightweight SQL analytical database
without requiring a separate database server.

The generated database is stored at:

`warehouse/warehouse.duckdb`

The warehouse directory is excluded from Git because the database is a
generated pipeline output and can be rebuilt from the clean data.

## 2. Three fact tables

Three fact tables are maintained because the NHS datasets have different
grains and date ranges:

- `fact_appointments_monthly` - ICB, month, appointment status, staff type,
  appointment mode and booking-wait band.
- `fact_appointments_by_category` - Sub-ICB, day, service setting and
  national category.
- `fact_appointments_by_duration` - Sub-ICB, day and duration band.

Combining these datasets into one fact table would mix different grains and
could cause duplicated appointment counts.

## 3. Dimension tables

Five dimensions are used:

- `dim_geography`
- `dim_date`
- `dim_booking_wait`
- `dim_duration_band`
- `dim_national_category`

Existing NHS codes and labels are retained rather than creating unnecessary
surrogate identifiers.

## 4. Date dimension

`dim_date` contains one row per calendar day from 2020-01-01 through
2022-12-31.

This produces 1,096 unique dates with no gaps or duplicates.

## 5. Idempotent warehouse loading

Warehouse tables are rebuilt using `CREATE OR REPLACE TABLE` inside a DuckDB
transaction.

This makes the final warehouse state idempotent: rerunning the load does not
append duplicate rows or increase appointment totals.

The warehouse load was executed three times and produced identical results:

- Regional rows: 295,692
- Regional appointments: 742,804,525
- Category appointments: 296,046,770
- Duration appointments: 167,980,692

The complete Extract -> Transform -> Load -> Quality Checks pipeline was also
executed three consecutive times successfully with exit code 0.

## 6. Quality assurance

Nine automated quality checks are executed after loading.

They validate:

1. Monthly fact appointment total.
2. Category fact appointment total.
3. Duration fact appointment total.
4. Monthly reconciliation between regional and category datasets.
5. Geography referential integrity.
6. Booking-wait dimension coverage.
7. Duration-band dimension coverage.
8. Null dates and appointment counts in the category fact.
9. Monthly duration coverage compared with category appointments.

All nine checks pass.

The lowest monthly duration coverage is 90.90%, which is above the required
90% threshold.

The machine-readable results are written to:

`docs/quality_report.json`

## 7. Pipeline automation

`run_pipeline.py` executes the project stages in the following order:

`Extract -> Transform -> Load -> Quality Checks`

The pipeline uses these exit codes:

- `0` - pipeline completed successfully.
- `1` - unexpected pipeline failure.
- `2` - quality validation failure.

Pipeline execution is also recorded in `logs/pipeline.log`.

## 8. Generated files and Git

Generated and local files are excluded from version control, including:

- `data/raw/`
- `data/clean/`
- `warehouse/`
- `.venv/`
- `__pycache__/`

The DuckDB warehouse is therefore reproducible from the pipeline rather than
being stored in the Git repository.
