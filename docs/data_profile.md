
# NHS GP Appointments - Week 1 Data Profile

## 1. appointments_regional.csv

- Rows: 596,821
- Columns: 7
- Null values: 0
- Date range: January 2020 to June 2022

### Columns

- icb_ons_code
- appointment_month
- appointment_status
- hcp_type
- appointment_mode
- time_between_book_and_appointment
- count_of_appointments

### Grain

One row represents a combination of:

ICB + month + appointment status + HCP/staff type +
appointment mode + booking-wait band.

The count_of_appointments column contains the number of appointments
for that combination.


## 2. national_categories.csv

- Rows: 817,394
- Columns: 8
- Null values: 0
- Date range: 1 August 2021 to 30 June 2022

### Columns

- appointment_date
- icb_ons_code
- sub_icb_location_name
- service_setting
- context_type
- national_category
- count_of_appointments
- appointment_month

### Grain

One row represents a combination of:

Sub-ICB location + day + service setting + national category.

The count_of_appointments column contains the number of appointments
for that combination.


## 3. actual_duration.csv

- Rows: 137,793
- Columns: 8
- Null values: 0
- Profiled date range: 12 January 2021 to 6 December 2022

### Columns

- sub_icb_location_code
- sub_icb_location_ons_code
- sub_icb_location_name
- icb_ons_code
- region_ons_code
- appointment_date
- actual_duration
- count_of_appointments

### Grain

One row represents a combination of:

Sub-ICB location + day + duration band.

The count_of_appointments column contains the number of appointments
for that combination.


## Data Quality Issues Identified

Five important issues were identified during Week 1 profiling:

1. The original actual-duration file is an Excel file despite its
   unusual .csv.xlsx filename.

2. The national categories file can contain a hidden byte-order mark
   (BOM) in the first column name.

3. Dates need careful parsing, including day-first date handling.

4. Duplicate-looking rows in the regional dataset must not simply
   be deleted because they represent real appointment counts that
   need to be aggregated correctly.

5. Some categorical labels contain inconsistent spelling or spacing,
   including double spaces and variations of "Other Practice Staff".

These issues will be handled during the Week 2 transformation stage.
