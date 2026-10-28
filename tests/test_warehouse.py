
import sys
from pathlib import Path

import duckdb
import pytest

PROJECT_DIR = Path("/content/drive/MyDrive/NHS_ETL_Project")
SRC_DIR = PROJECT_DIR / "src"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import config
import load


def connect():
    return duckdb.connect(str(config.WAREHOUSE_DB))


def test_fact_totals():
    con = connect()

    try:
        regional = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_monthly
        """).fetchone()[0]

        categories = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_by_category
        """).fetchone()[0]

        duration = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_by_duration
        """).fetchone()[0]

        assert regional == config.EXPECTED["regional"]["total"]
        assert categories == config.EXPECTED["categories"]["total"]
        assert duration == config.EXPECTED["duration"]["total"]

    finally:
        con.close()


def test_no_geography_orphans():
    con = connect()

    try:
        category_orphans = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_by_category f
            LEFT JOIN dim_geography g
              ON f.icb_code = g.icb_code
             AND f.sub_icb_location = g.sub_icb_location
            WHERE g.sub_icb_location IS NULL
        """).fetchone()[0]

        duration_orphans = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_by_duration f
            LEFT JOIN dim_geography g
              ON f.icb_code = g.icb_code
             AND f.sub_icb_location = g.sub_icb_location
            WHERE g.sub_icb_location IS NULL
        """).fetchone()[0]

        assert category_orphans == 0
        assert duration_orphans == 0

    finally:
        con.close()


def test_all_booking_wait_bands_exist():
    con = connect()

    try:
        unknown = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_monthly f
            LEFT JOIN dim_booking_wait d
              ON f.booking_wait = d.booking_wait
            WHERE d.booking_wait IS NULL
        """).fetchone()[0]

        assert unknown == 0

    finally:
        con.close()


def test_all_duration_bands_exist():
    con = connect()

    try:
        unknown = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_by_duration f
            LEFT JOIN dim_duration_band d
              ON f.duration_band = d.duration_band
            WHERE d.duration_band IS NULL
        """).fetchone()[0]

        assert unknown == 0

    finally:
        con.close()


def test_date_dimension_complete():
    con = connect()

    try:
        result = con.execute("""
            SELECT
                COUNT(*) AS rows,
                COUNT(DISTINCT date) AS unique_dates,
                MIN(date) AS min_date,
                MAX(date) AS max_date
            FROM dim_date
        """).fetchone()

        assert result[0] == 1096
        assert result[1] == 1096
        assert str(result[2]) == "2020-01-01"
        assert str(result[3]) == "2022-12-31"

    finally:
        con.close()


def test_load_is_idempotent():
    first = load.load_warehouse()
    second = load.load_warehouse()

    assert first == second


def require_expected_total(actual, expected):
    assert actual == expected, (
        f"actual total {actual:,} != expected {expected:,}"
    )


def test_broken_total_check_fails():
    expected = config.EXPECTED["regional"]["total"]

    # Deliberately incorrect value proves the check can fail.
    broken_total = expected - 1

    with pytest.raises(AssertionError):
        require_expected_total(broken_total, expected)
