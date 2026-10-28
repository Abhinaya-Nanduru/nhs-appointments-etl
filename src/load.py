
import sys
from pathlib import Path
import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import config


def create_dimensions(con):
    """Create the five Week 3 dimension tables."""

    # 1. Date dimension: every day from 2020 through 2022
    con.execute("""
        CREATE OR REPLACE TABLE dim_date AS
        SELECT
            CAST(d AS DATE) AS date,
            YEAR(d) AS year,
            MONTH(d) AS month,
            MONTHNAME(d) AS month_name,
            DAY(d) AS day,
            DAYOFWEEK(d) AS day_of_week,
            DAYNAME(d) AS weekday
        FROM generate_series(
            DATE '2020-01-01',
            DATE '2022-12-31',
            INTERVAL 1 DAY
        ) AS t(d)
    """)

    # 2. Geography dimension
    con.execute(f"""
        CREATE OR REPLACE TABLE dim_geography AS

        SELECT DISTINCT
            icb_ons_code AS icb_code,
            sub_icb_location_name AS sub_icb_location
        FROM read_parquet(
            '{config.CATEGORIES_CLEAN}/**/*.parquet',
            hive_partitioning = true
        )

        UNION

        SELECT DISTINCT
            icb_ons_code AS icb_code,
            sub_icb_location_name AS sub_icb_location
        FROM read_parquet(
            '{config.DURATION_CLEAN}/**/*.parquet',
            hive_partitioning = true
        )
    """)

    # 3. Booking-wait dimension
    con.execute(f"""
        CREATE OR REPLACE TABLE dim_booking_wait AS
        SELECT
            time_between_book_and_appointment AS booking_wait,
            ROW_NUMBER() OVER (
                ORDER BY MIN(month_start), time_between_book_and_appointment
            ) AS sort_order
        FROM read_parquet(
            '{config.REGIONAL_CLEAN}/**/*.parquet',
            hive_partitioning = true
        )
        GROUP BY time_between_book_and_appointment
    """)

    # 4. Duration-band dimension
    con.execute(f"""
        CREATE OR REPLACE TABLE dim_duration_band AS
        SELECT
            actual_duration AS duration_band,
            ROW_NUMBER() OVER (
                ORDER BY actual_duration
            ) AS sort_order
        FROM (
            SELECT DISTINCT actual_duration
            FROM read_parquet(
                '{config.DURATION_CLEAN}/**/*.parquet',
                hive_partitioning = true
            )
        )
    """)

    # 5. National-category dimension
    con.execute(f"""
        CREATE OR REPLACE TABLE dim_national_category AS
        SELECT DISTINCT
            national_category,
            context_type
        FROM read_parquet(
            '{config.CATEGORIES_CLEAN}/**/*.parquet',
            hive_partitioning = true
        )
    """)


def load_dimensions():
    """Open the DuckDB warehouse and create dimensions."""

    config.WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(config.WAREHOUSE_DB))

    try:
        create_dimensions(con)

        print("5 dimension tables created successfully.")

        tables = con.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
        """).fetchall()

        print("\nWarehouse tables:")
        for table in tables:
            print(" -", table[0])

    finally:
        con.close()


if __name__ == "__main__":
    load_dimensions()


def create_facts(con):
    """Create the three Week 3 fact tables from Week 2 clean Parquet."""

    # -------------------------------------------------
    # 1. Monthly appointments fact
    # Grain:
    # ICB x month x status x staff type x mode x booking wait
    # -------------------------------------------------
    con.execute(f"""
        CREATE OR REPLACE TABLE fact_appointments_monthly AS
        SELECT
            icb_ons_code AS icb_code,
            CAST(month_start AS DATE) AS appointment_month,
            appointment_status AS status,
            hcp_type AS staff_type,
            appointment_mode AS mode,
            time_between_book_and_appointment AS booking_wait,
            count_of_appointments
        FROM read_parquet(
            '{config.REGIONAL_CLEAN}/**/*.parquet',
            hive_partitioning = true
        )
    """)

    # -------------------------------------------------
    # 2. Appointments by national category
    # Grain:
    # Sub-ICB x day x service setting x national category
    # -------------------------------------------------
    con.execute(f"""
        CREATE OR REPLACE TABLE fact_appointments_by_category AS
        SELECT
            icb_ons_code AS icb_code,
            sub_icb_location_name AS sub_icb_location,
            CAST(appointment_date_clean AS DATE) AS appointment_date,
            service_setting,
            context_type,
            national_category,
            count_of_appointments
        FROM read_parquet(
            '{config.CATEGORIES_CLEAN}/**/*.parquet',
            hive_partitioning = true
        )
    """)

    # -------------------------------------------------
    # 3. Appointments by duration
    # Grain:
    # Sub-ICB x day x duration band
    # -------------------------------------------------
    con.execute(f"""
        CREATE OR REPLACE TABLE fact_appointments_by_duration AS
        SELECT
            icb_ons_code AS icb_code,
            sub_icb_location_name AS sub_icb_location,
            CAST(appointment_date_clean AS DATE) AS appointment_date,
            actual_duration AS duration_band,
            count_of_appointments
        FROM read_parquet(
            '{config.DURATION_CLEAN}/**/*.parquet',
            hive_partitioning = true
        )
    """)

    print("3 fact tables created successfully.")


def load_warehouse():
    """Build/rebuild the complete Week 3 DuckDB warehouse."""

    config.WAREHOUSE_DIR.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(config.WAREHOUSE_DB))

    try:
        con.execute("BEGIN")

        # Rebuild dimensions from clean Parquet
        create_dimensions(con)

        # Rebuild facts from clean Parquet
        create_facts(con)

        # Validate critical warehouse totals before commit
        regional_rows = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_monthly
        """).fetchone()[0]

        regional_total = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_monthly
        """).fetchone()[0]

        categories_total = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_by_category
        """).fetchone()[0]

        duration_total = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_by_duration
        """).fetchone()[0]

        assert regional_rows == config.EXPECTED["regional"]["rows"], (
            f"Regional rows {regional_rows:,} != "
            f"{config.EXPECTED['regional']['rows']:,}"
        )

        assert regional_total == config.EXPECTED["regional"]["total"], (
            f"Regional total {regional_total:,} != "
            f"{config.EXPECTED['regional']['total']:,}"
        )

        assert categories_total == config.EXPECTED["categories"]["total"], (
            f"Categories total {categories_total:,} != "
            f"{config.EXPECTED['categories']['total']:,}"
        )

        assert duration_total == config.EXPECTED["duration"]["total"], (
            f"Duration total {duration_total:,} != "
            f"{config.EXPECTED['duration']['total']:,}"
        )

        con.execute("COMMIT")

        print("\nWAREHOUSE LOAD OK")
        print("=" * 60)
        print(f"Regional rows:       {regional_rows:,}")
        print(f"Regional total:      {regional_total:,}")
        print(f"Categories total:    {categories_total:,}")
        print(f"Duration total:      {duration_total:,}")
        print("Dimensions:          5")
        print("Facts:               3")
        print("=" * 60)

        return {
            "regional_rows": regional_rows,
            "regional_total": regional_total,
            "categories_total": categories_total,
            "duration_total": duration_total
        }

    except Exception:
        con.execute("ROLLBACK")
        raise

    finally:
        con.close()
