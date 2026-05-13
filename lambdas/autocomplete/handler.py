import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.opensearch_client import get_client, INDEX_NAME
from shared.utils import api_response, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

MAX_SUGGESTIONS = 8


def handler(event, context):
    params = event.get("queryStringParameters") or {}
    prefix = (params.get("q") or "").strip()

    if len(prefix) < 2:
        return api_response(200, {"suggestions": []})

    try:
        client = get_client()
        query = {
            "size": 0,
            "suggest": {
                "title_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "title.keyword",
                        "size": MAX_SUGGESTIONS,
                        "skip_duplicates": True,
                    },
                },
                "company_suggest": {
                    "prefix": prefix,
                    "completion": {
                        "field": "company",
                        "size": MAX_SUGGESTIONS // 2,
                        "skip_duplicates": True,
                    },
                },
            },
            # Fallback: prefix match on title keyword
            "query": {
                "bool": {
                    "should": [
                        {"prefix": {"title.keyword": {"value": prefix, "boost": 2}}},
                        {"match_phrase_prefix": {"title": {"query": prefix}}},
                        {"prefix": {"company": {"value": prefix}}},
                    ]
                }
            },
            "_source": ["title", "company"],
        }

        raw = client.search(index=INDEX_NAME, body=query)

        # Collect suggestions from hits (more reliable than completion suggester on small indices)
        seen: set[str] = set()
        suggestions = []
        for hit in raw.get("hits", {}).get("hits", [])[:MAX_SUGGESTIONS]:
            src = hit["_source"]
            title = src.get("title", "")
            company = src.get("company", "")
            if title and title not in seen:
                suggestions.append({"type": "title", "value": title, "company": company})
                seen.add(title)

        return api_response(200, {"suggestions": suggestions})

    except Exception as e:
        logger.error("Autocomplete error: %s", e, exc_info=True)
        return api_response(500, {"error": "Internal server error"})
