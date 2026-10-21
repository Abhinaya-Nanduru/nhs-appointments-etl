
from pathlib import Path

PROJECT_DIR = Path("/content/drive/MyDrive/NHS_ETL_Project")

RAW_DIR = PROJECT_DIR / "data" / "raw"
CLEAN_DIR = PROJECT_DIR / "data" / "clean"

REGIONAL_FILE = RAW_DIR / "appointments_regional.csv"
CATEGORIES_FILE = RAW_DIR / "national_categories.csv"
DURATION_FILE = RAW_DIR / "actual_duration.csv.xlsx"

REGIONAL_CLEAN = CLEAN_DIR / "regional"
CATEGORIES_CLEAN = CLEAN_DIR / "categories"
DURATION_CLEAN = CLEAN_DIR / "duration"
