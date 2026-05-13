from __future__ import annotations
import logging
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://remoteok.io/api"
HEADERS = {"User-Agent": "JobLens/1.0 (job aggregator; contact abrahamjaimesdev@gmail.com)"}


def fetch_all() -> list[dict]:
    response = requests.get(BASE_URL, headers=HEADERS, timeout=20)
    response.raise_for_status()
    data = response.json()
    # First element is a legal disclaimer object, not a job
    jobs = [item for item in data if isinstance(item, dict) and item.get("position")]
    logger.info("RemoteOK total fetched: %d", len(jobs))
    return jobs
