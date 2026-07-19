"""
Run the full FinMark pipeline end to end:
1. Bronze profiling and raw-data ingestion
2. Silver cleaning and validation
3. Gold transformations
4. Resilience scenario test
"""

import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE_DIR / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_logger
import build_gold_layer
import clean_silver_layer
import profile_bronze_layer
import test_resilience_scenario


def main():
    logger = audit_logger.AuditLogger()
    logger.log_pipeline_start()
    
    try:
        # BRONZE LAYER
        print("=" * 80)
        print("RUNNING BRONZE LAYER")
        print("=" * 80)
        start_time = time.time()
        try:
            profile_bronze_layer.profile_all()
            duration = time.time() - start_time
            logger.log_event('BRONZE', 'SUCCESS', duration)
        except Exception as e:
            duration = time.time() - start_time
            logger.log_event('BRONZE', 'FAILURE', duration, str(e))
            raise

        # SILVER LAYER
        print("\n" + "=" * 80)
        print("RUNNING SILVER LAYER")
        print("=" * 80)
        start_time = time.time()
        try:
            clean_silver_layer.clean_all()
            duration = time.time() - start_time
            logger.log_event('SILVER', 'SUCCESS', duration)
        except Exception as e:
            duration = time.time() - start_time
            logger.log_event('SILVER', 'FAILURE', duration, str(e))
            raise

        # GOLD LAYER
        print("\n" + "=" * 80)
        print("RUNNING GOLD LAYER")
        print("=" * 80)
        start_time = time.time()
        try:
            build_gold_layer.build_all()
            duration = time.time() - start_time
            logger.log_event('GOLD', 'SUCCESS', duration)
        except Exception as e:
            duration = time.time() - start_time
            logger.log_event('GOLD', 'FAILURE', duration, str(e))
            raise

        # RESILIENCE TEST
        print("\n" + "=" * 80)
        print("RUNNING RESILIENCE TEST")
        print("=" * 80)
        start_time = time.time()
        try:
            test_resilience_scenario.main()
            duration = time.time() - start_time
            logger.log_event('RESILIENCE_TEST', 'SUCCESS', duration)
        except Exception as e:
            duration = time.time() - start_time
            logger.log_event('RESILIENCE_TEST', 'FAILURE', duration, str(e))
            raise

        logger.log_pipeline_end()
        print("\nFull pipeline completed successfully.")

    except Exception as e:
        logger.log_pipeline_failure(str(e))
        print(f"\nPipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
