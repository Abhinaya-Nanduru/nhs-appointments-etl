
import sys
from pathlib import Path

import pytest
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


PROJECT_DIR = Path(
    "/content/drive/MyDrive/NHS_ETL_Project"
)

CLEAN_DIR = PROJECT_DIR / "data" / "clean"


@pytest.fixture(scope="session")
def spark():

    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName("NHS_ETL_Tests")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    yield spark

    spark.stop()


def load_clean(spark, name):
    return spark.read.parquet(
        str(CLEAN_DIR / name)
    )


def total_appointments(df):

    return (
        df.agg(
            F.sum("count_of_appointments")
        )
        .first()[0]
    )


def test_regional_row_count(spark):

    df = load_clean(spark, "regional")

    assert df.count() == 295692


def test_regional_total(spark):

    df = load_clean(spark, "regional")

    assert total_appointments(df) == 742804525


def test_categories_total(spark):

    df = load_clean(spark, "categories")

    assert total_appointments(df) == 296046770


def test_duration_total(spark):

    df = load_clean(spark, "duration")

    assert total_appointments(df) == 167980692


def test_positive_regional_counts(spark):

    df = load_clean(spark, "regional")

    assert (
        df.filter(
            F.col("count_of_appointments") <= 0
        ).count()
        == 0
    )


def test_positive_categories_counts(spark):

    df = load_clean(spark, "categories")

    assert (
        df.filter(
            F.col("count_of_appointments") <= 0
        ).count()
        == 0
    )


def test_positive_duration_counts(spark):

    df = load_clean(spark, "duration")

    assert (
        df.filter(
            F.col("count_of_appointments") <= 0
        ).count()
        == 0
    )


def test_regional_month_dates(spark):

    df = load_clean(spark, "regional")

    assert (
        df.filter(
            F.col("month_start").isNull()
        ).count()
        == 0
    )


def test_categories_day_first_dates(spark):

    df = load_clean(spark, "categories")

    assert (
        df.filter(
            F.col("appointment_date_clean").isNull()
        ).count()
        == 0
    )


def test_duration_dates(spark):

    df = load_clean(spark, "duration")

    assert (
        df.filter(
            F.col("appointment_date_clean").isNull()
        ).count()
        == 0
    )


def test_regional_tidy_labels(spark):

    df = load_clean(spark, "regional")

    text_columns = [
        "appointment_status",
        "hcp_type",
        "appointment_mode",
        "time_between_book_and_appointment"
    ]

    for column in text_columns:

        bad_rows = df.filter(
            F.col(column).contains("  ")
        ).count()

        assert bad_rows == 0


def test_regional_unique_grain(spark):

    df = load_clean(spark, "regional")

    keys = [
        "icb_ons_code",
        "month_start",
        "appointment_status",
        "hcp_type",
        "appointment_mode",
        "time_between_book_and_appointment"
    ]

    duplicate_keys = (
        df.groupBy(*keys)
        .count()
        .filter(F.col("count") > 1)
        .count()
    )

    assert duplicate_keys == 0
