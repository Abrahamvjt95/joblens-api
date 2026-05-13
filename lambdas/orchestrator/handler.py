import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.utils import get_lambda_client, save_to_s3, today_key, setup_logging

setup_logging()
logger = logging.getLogger(__name__)

RAW_BUCKET = os.environ.get("S3_BUCKET_RAW", "joblens-raw")

FETCHER_FUNCTIONS = {
    "adzuna":    os.environ.get("LAMBDA_FETCHER_ADZUNA",    "joblens-fetcher-adzuna"),
    "themuse":   os.environ.get("LAMBDA_FETCHER_THEMUSE",   "joblens-fetcher-themuse"),
    "remotive":  os.environ.get("LAMBDA_FETCHER_REMOTIVE",  "joblens-fetcher-remotive"),
    "arbeitnow": os.environ.get("LAMBDA_FETCHER_ARBEITNOW", "joblens-fetcher-arbeitnow"),
    "himalayas": os.environ.get("LAMBDA_FETCHER_HIMALAYAS", "joblens-fetcher-himalayas"),
    "jobicy":    os.environ.get("LAMBDA_FETCHER_JOBICY",    "joblens-fetcher-jobicy"),
}


def _invoke_fetcher(client, source: str, function_name: str) -> dict:
    """Invoke a fetcher Lambda asynchronously and return invocation metadata."""
    logger.info("Invoking fetcher source=%s function=%s", source, function_name)
    response = client.invoke(
        FunctionName=function_name,
        InvocationType="Event",   # async — fire and forget
        Payload=json.dumps({"source": source}),
    )
    status = response.get("StatusCode", 0)
    logger.info("Invoked source=%s status=%d", source, status)
    return {"source": source, "status": status, "invoked": status == 202}


def handler(event, context):
    """
    Triggered by EventBridge cron (daily).
    Invokes each fetcher Lambda asynchronously — fan-out pattern.
    Each fetcher saves its results to S3, which triggers the normalizer.
    """
    lambda_client = get_lambda_client()
    results = []

    for source, function_name in FETCHER_FUNCTIONS.items():
        result = _invoke_fetcher(lambda_client, source, function_name)
        results.append(result)

    invoked = sum(1 for r in results if r["invoked"])
    logger.info("Orchestrator done: %d/%d fetchers invoked", invoked, len(results))
    return {"invoked": invoked, "total": len(results), "results": results}
