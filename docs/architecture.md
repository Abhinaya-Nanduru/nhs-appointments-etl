
# NHS GP Appointments Pipeline Architecture

## ETL Architecture

NHS Source Files
        |
        v
+-------------------+
|    RAW LAYER      |
|    data/raw/      |
+-------------------+
        |
        | extract.py
        v
+-------------------+
| TRANSFORM / CLEAN |
|   transform.py    |
+-------------------+
        |
        v
+-------------------+
|   CLEAN LAYER     |
|   data/clean/     |
|     Parquet       |
+-------------------+
        |
        | Week 3
        v
+-------------------+
| DATA WAREHOUSE    |
+-------------------+
        |
        +-------------------------------+
        |               |               |
        v               v               v
 fact_appointments  fact_appointments  fact_appointments
     _monthly          _by_category       _by_duration
        |               |               |
        +---------------+---------------+
                        |
                        v
                  DIMENSIONS
          Date / Geography / Bands /
             National Category
                        |
                        v
                 Monthly KPI Pack


## Week 2 Pipeline

run_pipeline.py
      |
      +--> extract.py
      |       |
      |       +--> data/raw/
      |
      +--> transform.py
              |
              +--> Clean Regional
              +--> Clean Categories
              +--> Clean Duration
                       |
                       v
                  data/clean/
                 Parquet files


## Layer Responsibilities

### Raw Layer
Stores unchanged copies of the NHS source data.

### Clean Layer
Contains cleaned, standardised and validated data written as Parquet and partitioned by month.

### Warehouse Layer
Will be implemented in Week 3 using the three fact tables and conformed dimensions.

## Design Principle

Each layer reads from the layer above it. Raw data is never manually edited. If a derived layer is incorrect, it should be rebuilt from its upstream layer rather than patched manually.
