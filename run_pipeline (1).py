
import logging
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"

if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extract import extract
from transform import transform
from load import load_warehouse
from quality_checks import run_quality_checks


LOG_DIR = PROJECT_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "pipeline.log"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE)
    ]
)

logger = logging.getLogger(__name__)


def run_stage(stage_name, function):
    """Run one pipeline stage and record its duration."""

    logger.info("=" * 60)
    logger.info("STARTING: %s", stage_name)

    start = time.time()

    result = function()

    duration = time.time() - start

    logger.info(
        "COMPLETED: %s | duration=%.2f seconds",
        stage_name,
        duration
    )

    return result


def run_pipeline():
    """Run the complete NHS GP Appointments ETL pipeline."""

    logger.info("=" * 60)
    logger.info("NHS GP APPOINTMENTS PIPELINE STARTED")
    logger.info("=" * 60)

    try:

        # Stage 1
        run_stage(
            "EXTRACT",
            extract
        )

        # Stage 2
        run_stage(
            "TRANSFORM",
            transform
        )

        # Stage 3
        warehouse_result = run_stage(
            "LOAD",
            load_warehouse
        )

        # Stage 4
        quality_result = run_stage(
            "QUALITY CHECKS",
            run_quality_checks
        )

        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info(
            "Regional rows: %s",
            f"{warehouse_result['regional_rows']:,}"
        )
        logger.info(
            "Regional appointments: %s",
            f"{warehouse_result['regional_total']:,}"
        )
        logger.info(
            "Category appointments: %s",
            f"{warehouse_result['categories_total']:,}"
        )
        logger.info(
            "Duration appointments: %s",
            f"{warehouse_result['duration_total']:,}"
        )
        logger.info(
            "Quality checks: %s/%s passed",
            quality_result["summary"]["passed"],
            quality_result["summary"]["total_checks"]
        )
        logger.info("EXIT CODE: 0")
        logger.info("=" * 60)

        return 0

    except AssertionError as exc:

        logger.error("=" * 60)
        logger.error("PIPELINE STOPPED BY QUALITY CHECK")
        logger.error("%s", exc)
        logger.error("EXIT CODE: 2")
        logger.error("=" * 60)

        return 2

    except Exception:

        logger.exception("=" * 60)
        logger.error("PIPELINE CRASHED")
        logger.error("EXIT CODE: 1")
        logger.error("=" * 60)

        return 1


if __name__ == "__main__":
    sys.exit(run_pipeline())
