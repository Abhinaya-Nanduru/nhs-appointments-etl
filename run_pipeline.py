
import logging
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from extract import extract
from transform import transform


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


def run_pipeline():
    """Run the NHS GP appointments ETL pipeline."""

    logger.info("======================================")
    logger.info("NHS GP Appointments Pipeline Started")
    logger.info("======================================")

    try:
        logger.info("Stage 1: Extract")
        extract()

        logger.info("Stage 2: Transform")
        transform()

        logger.info("======================================")
        logger.info("Pipeline completed successfully")
        logger.info("======================================")

    except Exception:
        logger.exception("Pipeline failed")
        raise


if __name__ == "__main__":
    run_pipeline()
