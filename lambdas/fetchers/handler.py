"""
Single entry-point Lambda handler for all fetchers.
The source is passed in the event payload by the orchestrator.
Each source is deployed as a separate Lambda function pointing to this handler.
"""
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.utils import save_to_s3, today_key, setup_logging
from fetchers import adzuna, themuse, remotive, arbeitnow

setup_logging()
logger = logging.getLogger(__name__)

RAW_BUCKET = os.environ.get("S3_BUCKET_RAW", "joblens-raw")

_FETCHERS = {
    "adzuna":    adzuna.fetch_all,
    "themuse":   themuse.fetch_all,
    "remotive":  remotive.fetch_all,
    "arbeitnow": arbeitnow.fetch_all,
}


def handler(event, context):
    source = event.get("source") or os.environ.get("FETCHER_SOURCE", "")
    if not source or source not in _FETCHERS:
        raise ValueError(f"Unknown or missing source: '{source}'")

    logger.info("Starting fetch source=%s", source)
    jobs = _FETCHERS[source]()

    if not jobs:
        logger.warning("No jobs fetched for source=%s", source)
        return {"source": source, "fetched": 0}

    key = today_key(source, prefix="raw")
    save_to_s3(RAW_BUCKET, key, jobs)
    logger.info("Saved source=%s count=%d key=%s", source, len(jobs), key)
    return {"source": source, "fetched": len(jobs), "key": key}
