from __future__ import annotations
import json
import logging
import os
import boto3
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


def get_s3_client():
    return boto3.client(
        "s3",
        region_name=os.environ.get("AWS_REGION", "eu-west-1"),
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),  # LocalStack in dev
    )


def get_lambda_client():
    return boto3.client(
        "lambda",
        region_name=os.environ.get("AWS_REGION", "eu-west-1"),
        endpoint_url=os.environ.get("AWS_ENDPOINT_URL"),
    )


def save_to_s3(bucket: str, key: str, data: list[dict]) -> None:
    s3 = get_s3_client()
    body = json.dumps(data, ensure_ascii=False, default=str)
    s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")
    logger.info("Saved %d records to s3://%s/%s", len(data), bucket, key)


def load_from_s3(bucket: str, key: str) -> list[dict]:
    s3 = get_s3_client()
    response = s3.get_object(Bucket=bucket, Key=key)
    return json.loads(response["Body"].read())


def today_key(source: str, prefix: str = "raw") -> str:
    """Returns a dated S3 key like raw/adzuna/2026-05-13.json"""
    return f"{prefix}/{source}/{date.today().isoformat()}.json"


def api_response(status_code: int, body: Any, headers: dict | None = None) -> dict:
    """Standard API Gateway response format."""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    return {
        "statusCode": status_code,
        "headers": {**default_headers, **(headers or {})},
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format='{"time": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
    )
