# NHS GP Appointments Star Schema Design

## Fact Table 1: fact_appointments_monthly

**Grain:**

One row represents:

ICB × Month × Appointment Status × Staff Type × Appointment Mode × Booking-Wait Band

**Measure:**

- count_of_appointments

**Supports KPIs:**

1-8

---

## Fact Table 2: fact_appointments_by_category

**Grain:**

One row represents:

Sub-ICB Location × Day × Service Setting × National Category

**Measure:**

- count_of_appointments

**Supports KPIs:**

9, 10 and 12

---

## Fact Table 3: fact_appointments_by_duration

**Grain:**

One row represents:

Sub-ICB Location × Day × Duration Band

**Measure:**

- count_of_appointments

**Supports KPIs:**

11 and 12

---

# Dimensions

The proposed warehouse dimensions are:

## dim_date

Contains calendar attributes such as:

- Date
- Month
- Year
- Weekday

## dim_geography

Contains:

- Sub-ICB
- ICB
- Region

## dim_booking_wait

Contains booking-wait bands and their sort order.

## dim_duration

Contains appointment-duration bands and their sort order.

## dim_national_category

Contains national appointment categories and their context type.

---

# Design Rules

The three fact tables will not be joined directly row by row because they have different grains.

Appointment counts will be stored as additive measures.

Rates and percentages will be calculated when querying the warehouse rather than stored as fact-table measures.

Shared dimensions will be conformed across the relevant fact tables.

Booking-wait and duration bands will have explicit sort orders so they display in their logical order rather than alphabetical order.
