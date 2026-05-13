from __future__ import annotations
import logging
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.opensearch_client import get_client
from shared.utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

INDEX = os.environ.get("OPENSEARCH_INDEX", "job-listings")
TTL_DAYS = int(os.environ.get("JOBS_TTL_DAYS", "30"))


def handler(event, context):
    cutoff = (datetime.now(timezone.utc) - timedelta(days=TTL_DAYS)).strftime("%Y-%m-%d")
    client = get_client()

    response = client.delete_by_query(
        index=INDEX,
        body={"query": {"range": {"posted_at": {"lt": cutoff}}}},
        params={"conflicts": "proceed", "refresh": "true"},
    )

    deleted = response.get("deleted", 0)
    total_before = client.count(index=INDEX)["count"]
    logger.info("Cleanup: deleted=%d older_than=%s remaining=%d", deleted, cutoff, total_before)
    return {"deleted": deleted, "cutoff": cutoff, "remaining": total_before}
