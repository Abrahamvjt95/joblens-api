import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.opensearch_client import get_client, INDEX_NAME
from shared.utils import api_response, setup_logging
from search.query_builder import build_query, parse_response

setup_logging()
logger = logging.getLogger(__name__)


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    logger.info("Search params: %s", params)

    try:
        client = get_client()
        query = build_query(params)
        raw = client.search(index=INDEX_NAME, body=query)
        result = parse_response(raw)
        return api_response(200, result)

    except ValueError as e:
        return api_response(400, {"error": str(e)})
    except Exception as e:
        logger.error("Search error: %s", e, exc_info=True)
        return api_response(500, {"error": "Internal server error"})
