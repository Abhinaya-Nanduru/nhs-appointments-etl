import csv
import hashlib
import json
import shutil
from datetime import datetime,timezone
from pathlib import  Path

import pandas as pd
source_dir=Path('/content/drive/MyDrive/Data')
project_dir=Path('/content/drive/MyDrive/NHS_ETL_Project')
raw_dir=project_dir/'data'/'raw'
raw_dir.mkdir(parents=True,exist_ok=True)

files=["appointments_regional.csv",
       'national_categories.csv',
       'actual_duration.csv.xlsx',
       'metadata_nhs.txt',]

def calculate_sha256(file_path):
  """Calculate the SHA-256 checksum of a file\."""
  checksum=hashlib.sha256()
  with open(file_path,'rb') as file:
      for chunk in iter(lambda: file.read(1024*1024),b""):
          checksum.update(chunk)
  return checksum.hexdigest()
def count_rows(file_path):
  """Count data rows,excluding the header for CSV files."""
  suffix=file_path.suffix.lower()
  if suffix == ".csv":
        with open(file_path, "r", encoding="utf-8-sig", newline="") as file:
            return max(sum(1 for _ in csv.reader(file)) - 1, 0)

  if suffix == ".xlsx":
        return len(pd.read_excel(file_path))

  return None


def extract():
    manifest = {
        "source": "NHS England - Appointments in General Practice",
        "extraction_time_utc": datetime.now(timezone.utc).isoformat(),
        "files": [],
    }

    for filename in files:
        source_file = source_dir/ filename

        if not source_file.is_file():
            raise FileNotFoundError(
                f"Could not find {filename} in {source_dir}"
            )

        destination_file = raw_dir/ filename

        # Copy the original file without modifying it.
        shutil.copy2(source_file, destination_file)

        # Convert the Excel file into an additional CSV file.
        if filename == "actual_duration.csv.xlsx":
            excel_data = pd.read_excel(destination_file)

            csv_destination = raw_dir / "actual_duration.csv"
            excel_data.to_csv(csv_destination, index=False)

            print(f"Converted Excel file to {csv_destination.name}")

        record = {
            "file_name": destination_file.name,
            "size_bytes": destination_file.stat().st_size,
            "sha256": calculate_sha256(destination_file),
            "row_count": count_rows(destination_file),
            "extraction_time_utc": datetime.now(timezone.utc).isoformat(),
        }

        manifest["files"].append(record)

        print(f"Copied: {destination_file.name}")

    manifest_path = raw_dir / "manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)

    print(f"\nManifest created: {manifest_path}")
    print("Extraction completed successfully.")


if __name__ == "__main__":
    extract()
