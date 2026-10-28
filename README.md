

---

## Week 3 - DuckDB Warehouse and Pipeline Automation

Week 3 extends the NHS GP Appointments ETL project by loading the cleaned
Parquet datasets into a DuckDB analytical warehouse and automating the full
pipeline.

### Warehouse Model

The DuckDB warehouse contains three fact tables:

- `fact_appointments_monthly`
- `fact_appointments_by_category`
- `fact_appointments_by_duration`

The warehouse also contains five dimension tables:

- `dim_geography`
- `dim_date`
- `dim_booking_wait`
- `dim_duration_band`
- `dim_national_category`

The generated database is:

`warehouse/warehouse.duckdb`

The warehouse is not committed to Git because it can be rebuilt by the
pipeline.

### Automated Pipeline

The complete pipeline runs in this order:

`Extract -> Transform -> Load -> Quality Checks`

Run the project from the repository root using:

    python run_pipeline.py

A successful pipeline execution returns exit code `0`.

Pipeline logs are written to:

`logs/pipeline.log`

### Quality Checks

Nine automated quality checks validate:

1. Monthly fact appointment total.
2. Category fact appointment total.
3. Duration fact appointment total.
4. Regional/category monthly reconciliation.
5. Geography referential integrity.
6. Booking-wait dimension coverage.
7. Duration-band dimension coverage.
8. Null dates and appointment counts in the category fact.
9. Monthly duration coverage of at least 90%.

The machine-readable quality report is written to:

`docs/quality_report.json`

### Expected Warehouse Results

A successful load produces:

- Regional fact rows: `295,692`
- Regional appointments: `742,804,525`
- Category appointments: `296,046,770`
- Duration appointments: `167,980,692`
- Dimensions: `5`
- Facts: `3`
- Quality checks: `9/9 PASS`

### Running the Tests

Run the Week 3 tests from the repository root using:

    pytest tests/test_warehouse.py -v

The tests validate fact totals, dimension coverage, geography referential
integrity, the date dimension, repeatable loading and deliberate failure
detection.

### Clean Clone Setup

After cloning the repository:

1. Create or activate a Python environment.
2. Install the project dependencies.
3. Make the required NHS source files available to the extraction stage.
4. Run `python run_pipeline.py`.
5. Confirm that all nine quality checks pass.

The pipeline rebuilds the clean datasets and DuckDB warehouse before running
the automated quality checks.

Generated raw data, clean data and warehouse files are excluded from Git
using `.gitignore`.
