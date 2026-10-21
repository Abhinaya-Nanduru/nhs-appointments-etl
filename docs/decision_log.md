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
