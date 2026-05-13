from __future__ import annotations
import logging
import os
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.themuse.com/api/public/jobs"
API_KEY = os.environ.get("THEMUSE_API_KEY", "")
CATEGORIES = ["Software Engineer", "Data Science", "DevOps", "IT", "Product Management"]
PAGES = int(os.environ.get("THEMUSE_PAGES", "3"))


def fetch(category: str, page: int = 0) -> list[dict]:
    params = {"category": category, "page": page, "descending": "true", "level": ["Entry", "Mid", "Senior"]}
    if API_KEY:
        params["api_key"] = API_KEY
    response = requests.get(BASE_URL, params=params, timeout=15)
    response.raise_for_status()
    return response.json().get("results", [])


def fetch_all() -> list[dict]:
    all_jobs: list[dict] = []
    for category in CATEGORIES:
        for page in range(PAGES):
            try:
                jobs = fetch(category, page)
                all_jobs.extend(jobs)
                logger.info("TheMuse category=%s page=%d jobs=%d", category, page, len(jobs))
                if not jobs:
                    break
            except requests.HTTPError as e:
                logger.error("TheMuse error category=%s page=%d: %s", category, page, e)
                break
    logger.info("TheMuse total fetched: %d", len(all_jobs))
    return all_jobs
