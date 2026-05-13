from __future__ import annotations
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.utils import load_from_s3, setup_logging
from shared.opensearch_client import get_client, ensure_index, bulk_index, doc_exists

setup_logging()
logger = logging.getLogger(__name__)

NORMALIZED_BUCKET = os.environ.get("S3_BUCKET_NORMALIZED", "joblens-normalized")
BATCH_SIZE = int(os.environ.get("INDEX_BATCH_SIZE", "100"))


def _split_batches(items: list, size: int):
    for i in range(0, len(items), size):
        yield items[i : i + size]


def handler(event, context):
    """
    Triggered by S3 ObjectCreated on the normalized bucket.
    Deduplicates by doc ID and bulk-indexes into OpenSearch in batches.
    """
    client = get_client()
    ensure_index(client)

    records = event.get("Records", [])
    total_indexed = total_skipped = total_failed = 0

    for record in records:
        s3_key = record["s3"]["object"]["key"]
        logger.info("Indexing key=%s", s3_key)

        docs: list[dict] = load_from_s3(NORMALIZED_BUCKET, s3_key)
        new_docs = []

        for doc in docs:
            doc_id = doc.get("id")
            if doc_id and doc_exists(client, doc_id):
                total_skipped += 1
            else:
                new_docs.append(doc)

        logger.info("key=%s new=%d skipped=%d", s3_key, len(new_docs), total_skipped)

        for batch in _split_batches(new_docs, BATCH_SIZE):
            ok, failed = bulk_index(client, batch)
            total_indexed += ok
            total_failed += failed

    logger.info(
        "Indexer done: indexed=%d skipped=%d failed=%d",
        total_indexed, total_skipped, total_failed,
    )
    return {
        "indexed": total_indexed,
        "skipped": total_skipped,
        "failed": total_failed,
    }
