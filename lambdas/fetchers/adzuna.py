from __future__ import annotations
import logging
import os
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.adzuna.com/v1/api/jobs"
APP_ID = os.environ.get("ADZUNA_APP_ID", "")
APP_KEY = os.environ.get("ADZUNA_APP_KEY", "")
COUNTRIES = os.environ.get("ADZUNA_COUNTRIES", "gb,pt,de,es").split(",")
PAGES_PER_COUNTRY = int(os.environ.get("ADZUNA_PAGES", "3"))
RESULTS_PER_PAGE = 50
TECH_QUERY = "software developer engineer"


def fetch(country: str, page: int = 1) -> list[dict]:
    url = f"{BASE_URL}/{country}/search/{page}"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": TECH_QUERY,
        "category": "it-jobs",
        "content-type": "application/json",
        "salary_include_unknown": 1,
        "country": country,
    }
    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()
    jobs = data.get("results", [])
    # Attach country code for normalizer
    for job in jobs:
        job["country"] = country
    return jobs


def fetch_all() -> list[dict]:
    all_jobs: list[dict] = []
    for country in COUNTRIES:
        country = country.strip()
        for page in range(1, PAGES_PER_COUNTRY + 1):
            try:
                jobs = fetch(country, page)
                all_jobs.extend(jobs)
                logger.info("Adzuna country=%s page=%d jobs=%d", country, page, len(jobs))
                if len(jobs) < RESULTS_PER_PAGE:
                    break  # no more pages
            except requests.HTTPError as e:
                logger.error("Adzuna fetch error country=%s page=%d: %s", country, page, e)
                break
    logger.info("Adzuna total fetched: %d", len(all_jobs))
    return all_jobs
