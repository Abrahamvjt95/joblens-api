from __future__ import annotations
import os
import logging
from opensearchpy import OpenSearch, RequestsHttpConnection, helpers

logger = logging.getLogger(__name__)

INDEX_NAME = os.environ.get("OPENSEARCH_INDEX", "job-listings")

INDEX_MAPPING = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "analysis": {
            "analyzer": {
                "tech_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop"]
                }
            }
        }
    },
    "mappings": {
        "properties": {
            "id":               {"type": "keyword"},
            "title":            {"type": "text", "analyzer": "english",
                                 "fields": {"keyword": {"type": "keyword"}}},
            "company":          {"type": "keyword"},
            "description":      {"type": "text", "analyzer": "english"},
            "location":         {"type": "text",
                                 "fields": {"keyword": {"type": "keyword"}}},
            "country":          {"type": "keyword"},
            "remote_type":      {"type": "keyword"},
            "salary_min":       {"type": "integer"},
            "salary_max":       {"type": "integer"},
            "salary_currency":  {"type": "keyword"},
            "stack":            {"type": "keyword"},
            "experience_level": {"type": "keyword"},
            "posted_at":        {"type": "date"},
            "source":           {"type": "keyword"},
            "apply_url":        {"type": "keyword", "index": False},
        }
    }
}


def get_client() -> OpenSearch:
    host = os.environ.get("OPENSEARCH_HOST", "localhost")
    port = int(os.environ.get("OPENSEARCH_PORT", 9200))
    use_ssl = os.environ.get("OPENSEARCH_USE_SSL", "false").lower() == "true"

    return OpenSearch(
        hosts=[{"host": host, "port": port}],
        http_compress=True,
        use_ssl=use_ssl,
        verify_certs=False,
        connection_class=RequestsHttpConnection,
    )


def ensure_index(client: OpenSearch) -> None:
    if not client.indices.exists(index=INDEX_NAME):
        client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
        logger.info("Created index: %s", INDEX_NAME)


def bulk_index(client: OpenSearch, docs: list[dict]) -> tuple[int, int]:
    """Bulk index documents. Returns (success_count, failed_count)."""
    actions = [
        {
            "_index": INDEX_NAME,
            "_id": doc["id"],
            "_source": doc,
        }
        for doc in docs
    ]
    success, errors = helpers.bulk(client, actions, raise_on_error=False)
    if errors:
        logger.warning("Bulk index errors: %d failed", len(errors))
    return success, len(errors)


def doc_exists(client: OpenSearch, doc_id: str) -> bool:
    return client.exists(index=INDEX_NAME, id=doc_id)
