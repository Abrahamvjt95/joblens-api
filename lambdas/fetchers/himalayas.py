from __future__ import annotations
import logging
import os
import time
import requests

logger = logging.getLogger(__name__)

SEARCH_URL = "https://himalayas.app/jobs/api/search"
QUERIES = os.environ.get(
    "HIMALAYAS_QUERIES",
    "software engineer,backend developer,frontend developer,full stack,"
    "devops engineer,data engineer,python developer,javascript developer,"
    "cloud engineer,platform engineer,mobile developer,machine learning engineer",
).split(",")
PAGES_PER_QUERY = int(os.environ.get("HIMALAYAS_PAGES", "5"))


def fetch(query: str, page: int) -> list[dict]:
    response = requests.get(
        SEARCH_URL,
        params={"q": query.strip(), "page": page, "worldwide": "true"},
        timeout=20,
    )
    response.raise_for_status()
    return response.json().get("jobs", [])


def fetch_all() -> list[dict]:
    all_jobs: list[dict] = []
    seen_guids: set[str] = set()

    for query in QUERIES:
        for page in range(1, PAGES_PER_QUERY + 1):
            try:
                jobs = fetch(query, page)
                if not jobs:
                    break
                new = [j for j in jobs if j.get("guid") not in seen_guids]
                seen_guids.update(j.get("guid") for j in new if j.get("guid"))
                all_jobs.extend(new)
                logger.info("Himalayas q=%s page=%d new=%d", query, page, len(new))
                time.sleep(0.3)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 429:
                    logger.warning("Himalayas rate limited q=%s page=%d, waiting", query, page)
                    time.sleep(3)
                else:
                    logger.error("Himalayas error q=%s page=%d: %s", query, page, e)
                break

    logger.info("Himalayas total fetched: %d", len(all_jobs))
    return all_jobs
