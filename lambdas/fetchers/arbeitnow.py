from __future__ import annotations
import logging
import os
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://www.arbeitnow.com/api/job-board-api"
PAGES = int(os.environ.get("ARBEITNOW_PAGES", "3"))
TAGS = os.environ.get(
    "ARBEITNOW_TAGS", "python,java,angular,typescript,node,react,devops"
).split(",")


def fetch(page: int = 1) -> list[dict]:
    response = requests.get(BASE_URL, params={"page": page}, timeout=15)
    response.raise_for_status()
    return response.json().get("data", [])


def _is_tech_job(job: dict) -> bool:
    """Filter to tech-relevant jobs using tags or title keywords."""
    job_tags = [t.lower() for t in job.get("tags", [])]
    title = job.get("title", "").lower()
    for tag in TAGS:
        t = tag.strip().lower()
        if t in job_tags or t in title:
            return True
    return False


def fetch_all() -> list[dict]:
    all_jobs: list[dict] = []
    for page in range(1, PAGES + 1):
        try:
            jobs = fetch(page)
            if not jobs:
                break
            tech_jobs = [j for j in jobs if _is_tech_job(j)]
            all_jobs.extend(tech_jobs)
            logger.info("Arbeitnow page=%d total=%d tech=%d", page, len(jobs), len(tech_jobs))
        except requests.HTTPError as e:
            logger.error("Arbeitnow error page=%d: %s", page, e)
            break
    logger.info("Arbeitnow total fetched: %d", len(all_jobs))
    return all_jobs
