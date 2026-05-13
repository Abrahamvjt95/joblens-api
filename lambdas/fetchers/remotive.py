from __future__ import annotations
import logging
import os
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://remotive.com/api/remote-jobs"
CATEGORIES = os.environ.get(
    "REMOTIVE_CATEGORIES", "software-dev,devops-sysadmin,data,qa"
).split(",")


def fetch(category: str) -> list[dict]:
    response = requests.get(BASE_URL, params={"category": category}, timeout=15)
    response.raise_for_status()
    return response.json().get("jobs", [])


def fetch_all() -> list[dict]:
    all_jobs: list[dict] = []
    for category in CATEGORIES:
        category = category.strip()
        try:
            jobs = fetch(category)
            all_jobs.extend(jobs)
            logger.info("Remotive category=%s jobs=%d", category, len(jobs))
        except requests.HTTPError as e:
            logger.error("Remotive error category=%s: %s", category, e)
    logger.info("Remotive total fetched: %d", len(all_jobs))
    return all_jobs
