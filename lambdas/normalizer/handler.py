from __future__ import annotations
import json
import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.models import JobListing
from shared.utils import load_from_s3, save_to_s3, today_key, setup_logging
from normalizer.salary_parser import parse_salary
from normalizer.stack_extractor import extract_stack, infer_experience_level, infer_remote_type

setup_logging()
logger = logging.getLogger(__name__)

RAW_BUCKET = os.environ.get("S3_BUCKET_RAW", "joblens-raw")
NORMALIZED_BUCKET = os.environ.get("S3_BUCKET_NORMALIZED", "joblens-normalized")

# Source-specific normalizer functions
def _normalize_adzuna(raw: dict) -> JobListing | None:
    try:
        title = raw.get("title", "").strip()
        company = raw.get("company", {}).get("display_name", "Unknown")
        description = raw.get("description", "")
        location = raw.get("location", {}).get("display_name", "")
        country_code = raw.get("country", "gb").upper()
        apply_url = raw.get("redirect_url", "")
        salary_min, salary_max, currency = parse_salary(
            raw.get("salary_min"), raw.get("salary_max"), "GBP"
        )
        remote_type = infer_remote_type(f"{title} {description}")
        if raw.get("contract_type") == "permanent" and "remote" in description.lower():
            remote_type = infer_remote_type(description)

        return JobListing(
            title=title,
            company=company,
            description=description,
            location=location,
            country=country_code,
            remote_type=remote_type,
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            stack=extract_stack(f"{title} {description}"),
            experience_level=infer_experience_level(title),
            posted_at=raw.get("created", "")[:10] or None,
            source="adzuna",
            apply_url=apply_url,
        )
    except Exception as e:
        logger.warning("Adzuna normalize error: %s | %s", e, raw.get("id"))
        return None


def _normalize_themuse(raw: dict) -> JobListing | None:
    try:
        title = raw.get("name", "").strip()
        company = raw.get("company", {}).get("name", "Unknown")
        description = raw.get("contents", "")
        locations = raw.get("locations", [])
        location = locations[0].get("name", "") if locations else ""
        remote_type = "remote" if any("remote" in l.get("name", "").lower() for l in locations) else infer_remote_type(description)
        levels = raw.get("levels", [])
        exp_label = levels[0].get("name", "").lower() if levels else ""
        exp_map = {"entry": "junior", "mid": "mid", "senior": "senior", "management": "senior"}
        experience_level = exp_map.get(exp_label) or infer_experience_level(title)
        apply_url = raw.get("refs", {}).get("landing_page", "")

        return JobListing(
            title=title,
            company=company,
            description=description,
            location=location,
            country="US",
            remote_type=remote_type,
            stack=extract_stack(f"{title} {description}"),
            experience_level=experience_level,
            posted_at=raw.get("publication_date", "")[:10] or None,
            source="themuse",
            apply_url=apply_url,
        )
    except Exception as e:
        logger.warning("TheMuse normalize error: %s", e)
        return None


def _normalize_remotive(raw: dict) -> JobListing | None:
    try:
        salary_min, salary_max, currency = parse_salary(raw.get("salary"))
        return JobListing(
            title=raw.get("title", "").strip(),
            company=raw.get("company_name", "Unknown"),
            description=raw.get("description", ""),
            location=raw.get("candidate_required_location", "Worldwide"),
            country="",
            remote_type="remote",
            salary_min=salary_min,
            salary_max=salary_max,
            salary_currency=currency,
            stack=extract_stack(
                f"{raw.get('title', '')} {raw.get('description', '')}",
                existing_tags=raw.get("tags", []),
            ),
            experience_level=infer_experience_level(raw.get("title", "")),
            posted_at=raw.get("publication_date", "")[:10] or None,
            source="remotive",
            apply_url=raw.get("url", ""),
        )
    except Exception as e:
        logger.warning("Remotive normalize error: %s", e)
        return None


def _normalize_arbeitnow(raw: dict) -> JobListing | None:
    try:
        description = raw.get("description", "")
        return JobListing(
            title=raw.get("title", "").strip(),
            company=raw.get("company_name", "Unknown"),
            description=description,
            location=raw.get("location", ""),
            country="DE",
            remote_type="remote" if raw.get("remote") else infer_remote_type(description),
            stack=extract_stack(
                f"{raw.get('title', '')} {description}",
                existing_tags=raw.get("tags", []),
            ),
            experience_level=infer_experience_level(raw.get("title", "")),
            posted_at=raw.get("created_at", "")[:10] or None,
            source="arbeitnow",
            apply_url=raw.get("url", ""),
        )
    except Exception as e:
        logger.warning("Arbeitnow normalize error: %s", e)
        return None


_NORMALIZERS = {
    "adzuna": _normalize_adzuna,
    "themuse": _normalize_themuse,
    "remotive": _normalize_remotive,
    "arbeitnow": _normalize_arbeitnow,
}


def normalize_batch(source: str, raw_jobs: list[dict]) -> list[dict]:
    normalizer = _NORMALIZERS.get(source)
    if not normalizer:
        raise ValueError(f"Unknown source: {source}")

    results, skipped = [], 0
    seen_ids: set[str] = set()

    for raw in raw_jobs:
        job = normalizer(raw)
        if job is None:
            skipped += 1
            continue
        if job.id in seen_ids:
            skipped += 1
            continue
        seen_ids.add(job.id)
        results.append(job.to_dict())

    logger.info("source=%s normalized=%d skipped=%d", source, len(results), skipped)
    return results


def handler(event, context):
    """
    Triggered by S3 ObjectCreated event on the raw bucket.
    Reads raw/<source>/YYYY-MM-DD.json, normalizes, saves to normalized bucket.
    """
    records = event.get("Records", [])
    total_normalized = 0

    for record in records:
        s3_key = record["s3"]["object"]["key"]
        parts = s3_key.replace("raw/", "").split("/")
        if len(parts) < 2:
            logger.warning("Unexpected key format: %s", s3_key)
            continue

        source = parts[0]
        logger.info("Normalizing source=%s key=%s", source, s3_key)

        raw_jobs = load_from_s3(RAW_BUCKET, s3_key)
        normalized = normalize_batch(source, raw_jobs)

        out_key = s3_key.replace("raw/", "normalized/")
        save_to_s3(NORMALIZED_BUCKET, out_key, normalized)
        total_normalized += len(normalized)

    return {"normalized": total_normalized}
