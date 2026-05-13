from __future__ import annotations
import logging
import os
import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://jobicy.com/api/v2/remote-jobs"
TAGS = os.environ.get(
    "JOBICY_TAGS", "python,javascript,java,devops,react,angular,backend,frontend,fullstack,data,cloud,aws"
).split(",")


def fetch(tag: str) -> list[dict]:
    response = requests.get(
        BASE_URL,
        params={"count": 50, "tag": tag.strip()},
        timeout=15,
    )
    response.raise_for_status()
    return response.json().get("jobs", [])


def fetch_all() -> list[dict]:
    all_jobs: list[dict] = []
    seen_ids: set = set()
    for tag in TAGS:
        try:
            jobs = fetch(tag)
            new = [j for j in jobs if j.get("id") not in seen_ids]
            seen_ids.update(j.get("id") for j in new)
            all_jobs.extend(new)
            logger.info("Jobicy tag=%s jobs=%d new=%d", tag, len(jobs), len(new))
        except requests.HTTPError as e:
            logger.error("Jobicy error tag=%s: %s", tag, e)
    logger.info("Jobicy total fetched: %d", len(all_jobs))
    return all_jobs
