
import json
import sys
from pathlib import Path

import duckdb

PROJECT_DIR = Path(__file__).resolve().parent.parent

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import config


def run_quality_checks():
    """Run all nine Week 3 warehouse quality checks."""

    con = duckdb.connect(str(config.WAREHOUSE_DB))
    results = []

    def record(name, passed, detail):
        results.append({
            "check": name,
            "status": "PASS" if passed else "FAIL",
            "detail": detail
        })

    try:

        # -------------------------------------------------
        # CHECK 1 - Monthly fact total
        # -------------------------------------------------
        actual = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_monthly
        """).fetchone()[0]

        expected = config.EXPECTED["regional"]["total"]

        record(
            "1. Monthly fact total",
            actual == expected,
            f"actual={actual:,}, expected={expected:,}"
        )


        # -------------------------------------------------
        # CHECK 2 - Category fact total
        # -------------------------------------------------
        actual = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_by_category
        """).fetchone()[0]

        expected = config.EXPECTED["categories"]["total"]

        record(
            "2. Category fact total",
            actual == expected,
            f"actual={actual:,}, expected={expected:,}"
        )


        # -------------------------------------------------
        # CHECK 3 - Duration fact total
        # -------------------------------------------------
        actual = con.execute("""
            SELECT SUM(count_of_appointments)
            FROM fact_appointments_by_duration
        """).fetchone()[0]

        expected = config.EXPECTED["duration"]["total"]

        record(
            "3. Duration fact total",
            actual == expected,
            f"actual={actual:,}, expected={expected:,}"
        )


        # -------------------------------------------------
        # CHECK 4 - Monthly reconciliation
        # Aug 2021 through Jun 2022
        # -------------------------------------------------
        different_months = con.execute("""
            WITH regional AS (
                SELECT
                    appointment_month AS month,
                    SUM(count_of_appointments) AS total
                FROM fact_appointments_monthly
                WHERE appointment_month BETWEEN
                      DATE '2021-08-01' AND DATE '2022-06-01'
                GROUP BY appointment_month
            ),
            category AS (
                SELECT
                    DATE_TRUNC('month', appointment_date) AS month,
                    SUM(count_of_appointments) AS total
                FROM fact_appointments_by_category
                WHERE appointment_date >= DATE '2021-08-01'
                  AND appointment_date < DATE '2022-07-01'
                GROUP BY 1
            )
            SELECT COUNT(*)
            FROM regional r
            JOIN category c USING (month)
            WHERE r.total <> c.total
        """).fetchone()[0]

        record(
            "4. Regional/category monthly reconciliation",
            different_months == 0,
            f"months_different={different_months}, expected=0"
        )


        # -------------------------------------------------
        # CHECK 5 - Geography orphans
        # -------------------------------------------------
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

        total_orphans = category_orphans + duration_orphans

        record(
            "5. Geography orphan rows",
            total_orphans == 0,
            f"category_orphans={category_orphans}, "
            f"duration_orphans={duration_orphans}, expected=0"
        )


        # -------------------------------------------------
        # CHECK 6 - Booking-wait bands
        # -------------------------------------------------
        unknown_wait = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_monthly f
            LEFT JOIN dim_booking_wait d
              ON f.booking_wait = d.booking_wait
            WHERE d.booking_wait IS NULL
        """).fetchone()[0]

        record(
            "6. Known booking-wait bands",
            unknown_wait == 0,
            f"unknown_rows={unknown_wait}, expected=0"
        )


        # -------------------------------------------------
        # CHECK 7 - Duration bands
        # -------------------------------------------------
        unknown_duration = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_by_duration f
            LEFT JOIN dim_duration_band d
              ON f.duration_band = d.duration_band
            WHERE d.duration_band IS NULL
        """).fetchone()[0]

        record(
            "7. Known duration bands",
            unknown_duration == 0,
            f"unknown_rows={unknown_duration}, expected=0"
        )


        # -------------------------------------------------
        # CHECK 8 - Category null dates/counts
        # -------------------------------------------------
        null_rows = con.execute("""
            SELECT COUNT(*)
            FROM fact_appointments_by_category
            WHERE appointment_date IS NULL
               OR count_of_appointments IS NULL
        """).fetchone()[0]

        record(
            "8. Category dates and counts not null",
            null_rows == 0,
            f"null_rows={null_rows}, expected=0"
        )


        # -------------------------------------------------
        # CHECK 9 - Duration coverage
        # -------------------------------------------------
        lowest_coverage = con.execute("""
            WITH category AS (
                SELECT
                    DATE_TRUNC('month', appointment_date) AS month,
                    SUM(count_of_appointments) AS total
                FROM fact_appointments_by_category
                GROUP BY 1
            ),
            duration AS (
                SELECT
                    DATE_TRUNC('month', appointment_date) AS month,
                    SUM(count_of_appointments) AS total
                FROM fact_appointments_by_duration
                GROUP BY 1
            )
            SELECT MIN(
                100.0 * d.total / c.total
            )
            FROM duration d
            JOIN category c USING (month)
        """).fetchone()[0]

        record(
            "9. Duration monthly coverage",
            lowest_coverage >= 90.0,
            f"lowest_coverage={lowest_coverage:.2f}%, expected>=90%"
        )

    finally:
        con.close()

    # -------------------------------------------------
    # Write JSON report
    # -------------------------------------------------
    report_path = PROJECT_DIR / "docs" / "quality_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "summary": {
            "total_checks": len(results),
            "passed": sum(r["status"] == "PASS" for r in results),
            "failed": sum(r["status"] == "FAIL" for r in results)
        },
        "checks": results
    }

    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Show every result before failing the run
    print("\nWEEK 3 QUALITY CHECKS")
    print("=" * 70)

    for result in results:
        print(
            f"{result['status']:<4} | "
            f"{result['check']} | "
            f"{result['detail']}"
        )

    passed = report["summary"]["passed"]
    failed = report["summary"]["failed"]

    print("=" * 70)
    print(f"Checks passed: {passed}/{len(results)}")
    print(f"Checks failed: {failed}/{len(results)}")
    print(f"Report: {report_path}")

    # Fail only after all checks have been recorded.
    if failed:
        raise AssertionError(
            f"{failed} warehouse quality check(s) failed."
        )

    return report


if __name__ == "__main__":
    run_quality_checks()
