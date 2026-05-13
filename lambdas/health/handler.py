import logging
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.opensearch_client import get_client, INDEX_NAME
from shared.utils import api_response, setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def handler(event, context):
    status = {"api": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}

    try:
        client = get_client()
        cluster = client.cluster.health()
        count = client.count(index=INDEX_NAME).get("count", 0)
        status["opensearch"] = cluster.get("status", "unknown")
        status["indexed_jobs"] = count
    except Exception as e:
        logger.warning("Health check OpenSearch error: %s", e)
        status["opensearch"] = "unavailable"
        status["indexed_jobs"] = 0

    http_status = 200 if status.get("opensearch") in ("green", "yellow") else 503
    return api_response(http_status, status)
