
import logging
import sys
from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    LongType
)

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import config


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def create_spark():

    spark = (
        SparkSession.builder
        .appName("NHS_GP_Appointments_ETL")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )

    return spark


def transform_regional(spark):

    logger.info("Starting regional transformation")

    schema = StructType([
        StructField("icb_ons_code", StringType(), True),
        StructField("appointment_month", StringType(), True),
        StructField("appointment_status", StringType(), True),
        StructField("hcp_type", StringType(), True),
        StructField("appointment_mode", StringType(), True),
        StructField("time_between_book_and_appointment", StringType(), True),
        StructField("count_of_appointments", LongType(), True),
    ])

    df = (
        spark.read
        .option("header", True)
        .schema(schema)
        .csv(str(config.REGIONAL_FILE))
    )

    raw_rows = df.count()

    raw_total = (
        df.agg(F.sum("count_of_appointments"))
        .first()[0]
    )

    # Clean text labels
    text_columns = [
        "appointment_status",
        "hcp_type",
        "appointment_mode",
        "time_between_book_and_appointment"
    ]

    for column in text_columns:
        df = df.withColumn(
            column,
            F.trim(F.regexp_replace(F.col(column), r"\s+", " "))
        )

    # Standardise Other Practice Staff
    df = df.withColumn(
        "hcp_type",
        F.when(
            F.lower(F.col("hcp_type")) == "other practice staff",
            F.lit("Other Practice Staff")
        ).otherwise(F.col("hcp_type"))
    )

    # Add month_start while keeping original column
    df = df.withColumn(
        "month_start",
        F.to_date(
            F.concat(F.col("appointment_month"), F.lit("-01")),
            "yyyy-MM-dd"
        )
    )

    # Sum look-alike rows - DO NOT simply drop them
    group_columns = [
        "icb_ons_code",
        "appointment_month",
        "month_start",
        "appointment_status",
        "hcp_type",
        "appointment_mode",
        "time_between_book_and_appointment"
    ]

    clean_df = (
        df.groupBy(*group_columns)
        .agg(
            F.sum("count_of_appointments")
            .alias("count_of_appointments")
        )
    )

    clean_rows = clean_df.count()

    clean_total = (
        clean_df.agg(F.sum("count_of_appointments"))
        .first()[0]
    )

    logger.info(
        "Regional rows: raw=%s clean=%s",
        raw_rows,
        clean_rows
    )

    logger.info(
        "Regional totals: raw=%s clean=%s",
        raw_total,
        clean_total
    )

    return clean_df


def transform_categories(spark):

    logger.info("Starting categories transformation")

    schema = StructType([
        StructField("appointment_date", StringType(), True),
        StructField("icb_ons_code", StringType(), True),
        StructField("sub_icb_location_name", StringType(), True),
        StructField("service_setting", StringType(), True),
        StructField("context_type", StringType(), True),
        StructField("national_category", StringType(), True),
        StructField("count_of_appointments", LongType(), True),
        StructField("appointment_month", StringType(), True),
    ])

    df = (
        spark.read
        .option("header", True)
        .option("encoding", "UTF-8")
        .schema(schema)
        .csv(str(config.CATEGORIES_FILE))
    )

    # Defensive removal of BOM from column names
    for old_name in df.columns:
        new_name = old_name.replace("\ufeff", "")
        if old_name != new_name:
            df = df.withColumnRenamed(old_name, new_name)

    # Parse source dates explicitly as day-first
    df = df.withColumn(
        "appointment_date_clean",
        F.to_date(F.col("appointment_date"), "dd/MM/yyyy")
    )

    # Keep original and add clean month column
    df = df.withColumn(
        "month_start",
        F.trunc(F.col("appointment_date_clean"), "month")
    )

    text_columns = [
        "sub_icb_location_name",
        "service_setting",
        "context_type",
        "national_category"
    ]

    for column in text_columns:
        df = df.withColumn(
            column,
            F.trim(F.regexp_replace(F.col(column), r"\s+", " "))
        )

    return df


def transform_duration(spark):

    logger.info("Starting duration transformation")

    # Duration source is Excel, so read it with pandas
    pdf = pd.read_excel(config.DURATION_FILE)

    # Clean column names
    pdf.columns = [
        str(column).replace("\ufeff", "").strip()
        for column in pdf.columns
    ]

    # Keep appointment counts as whole numbers
    pdf["count_of_appointments"] = (
        pd.to_numeric(
            pdf["count_of_appointments"],
            errors="raise"
        )
        .astype("int64")
    )

    # Parse Excel appointment dates safely in pandas
    pdf["appointment_date"] = pd.to_datetime(
        pdf["appointment_date"],
        dayfirst=True,
        errors="raise"
    )

    # Convert to Spark DataFrame
    df = spark.createDataFrame(pdf)

    # Clean labels
    df = df.withColumn(
        "actual_duration",
        F.trim(
            F.regexp_replace(
                F.col("actual_duration"),
                r"\s+",
                " "
            )
        )
    )

    df = df.withColumn(
        "sub_icb_location_name",
        F.trim(
            F.regexp_replace(
                F.col("sub_icb_location_name"),
                r"\s+",
                " "
            )
        )
    )

    # Parse date while retaining original value
    df = df.withColumn(
        "appointment_date_clean",
        F.to_date(F.col("appointment_date"))
    )

    df = df.withColumn(
        "month_start",
        F.trunc(F.col("appointment_date_clean"), "month")
    )

    return df


def validate_total(df, expected_total, dataset_name):

    total = (
        df.agg(F.sum("count_of_appointments"))
        .first()[0]
    )

    logger.info(
        "%s appointment total = %s",
        dataset_name,
        total
    )

    if total != expected_total:
        raise ValueError(
            f"{dataset_name}: expected total "
            f"{expected_total:,}, got {total:,}"
        )

    return total


def write_parquet(df, output_path):

    (
        df.write
        .mode("overwrite")
        .partitionBy("month_start")
        .parquet(str(output_path))
    )


def transform():

    spark = create_spark()

    try:

        regional = transform_regional(spark)
        categories = transform_categories(spark)
        duration = transform_duration(spark)

        # Required project totals
        validate_total(
            regional,
            742804525,
            "Regional"
        )

        validate_total(
            categories,
            296046770,
            "Categories"
        )

        validate_total(
            duration,
            167980692,
            "Duration"
        )

        regional_rows = regional.count()

        if regional_rows != 295692:
            raise ValueError(
                f"Regional clean rows should be 295,692, "
                f"but got {regional_rows:,}"
            )

        write_parquet(
            regional,
            config.REGIONAL_CLEAN
        )

        write_parquet(
            categories,
            config.CATEGORIES_CLEAN
        )

        write_parquet(
            duration,
            config.DURATION_CLEAN
        )

        logger.info("Transformation completed successfully")

        return [
            config.REGIONAL_CLEAN,
            config.CATEGORIES_CLEAN,
            config.DURATION_CLEAN
        ]

    finally:
        spark.stop()


if __name__ == "__main__":
    transform()
