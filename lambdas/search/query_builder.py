from __future__ import annotations
"""
Builds OpenSearch bool queries from filter parameters.
Demonstrates senior-level search: boosting, facets, aggregations, highlighting.
"""
from typing import Any


DEFAULT_SIZE = 20
MAX_SIZE = 100


def build_query(params: dict) -> dict:
    """
    Build a full OpenSearch search request body from query parameters.

    Supported params:
      q            - full-text query string
      stack        - comma-separated tech tags (filter)
      remote_type  - remote|hybrid|onsite (filter)
      country      - ISO country code (filter)
      source       - adzuna|themuse|remotive|arbeitnow (filter)
      experience   - junior|mid|senior (filter)
      salary_min   - minimum salary (range filter)
      salary_max   - maximum salary (range filter)
      page         - 1-based page number (default 1)
      size         - results per page (default 20)
      sort         - relevance|date|salary (default relevance)
    """
    q = (params.get("q") or "").strip()
    page = max(1, int(params.get("page", 1)))
    size = min(MAX_SIZE, int(params.get("size", DEFAULT_SIZE)))
    sort_by = params.get("sort", "relevance")

    must: list[dict] = []
    filters: list[dict] = []

    # ── Full-text query ──────────────────────────────────────────────────────
    if q:
        must.append({
            "multi_match": {
                "query": q,
                "fields": [
                    "title^4",          # title hits weighted 4x
                    "company^2",
                    "stack^3",
                    "description",
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",    # handles typos
                "minimum_should_match": "75%",
            }
        })
    else:
        must.append({"match_all": {}})

    # ── Keyword filters ──────────────────────────────────────────────────────
    def add_terms_filter(field: str, param: str, split: bool = False):
        value = params.get(param, "")
        if not value:
            return
        values = [v.strip() for v in value.split(",")] if split else [value.strip()]
        values = [v for v in values if v]
        if values:
            filters.append({"terms": {field: values}})

    add_terms_filter("stack", "stack", split=True)
    add_terms_filter("remote_type", "remote_type")
    add_terms_filter("country", "country")
    add_terms_filter("source", "source")
    add_terms_filter("experience_level", "experience")

    # ── Salary range filter ──────────────────────────────────────────────────
    salary_min = params.get("salary_min")
    salary_max = params.get("salary_max")
    if salary_min or salary_max:
        salary_range: dict[str, Any] = {}
        if salary_min:
            salary_range["gte"] = int(salary_min)
        if salary_max:
            salary_range["lte"] = int(salary_max)
        filters.append({"range": {"salary_min": salary_range}})

    # ── Sort ─────────────────────────────────────────────────────────────────
    sort_clause: list[dict] = []
    if sort_by == "date":
        sort_clause = [{"posted_at": {"order": "desc"}}, "_score"]
    elif sort_by == "salary":
        sort_clause = [{"salary_min": {"order": "desc", "missing": "_last"}}, "_score"]
    else:
        sort_clause = ["_score", {"posted_at": {"order": "desc"}}]

    # ── Aggregations (facets) ────────────────────────────────────────────────
    aggs = {
        "by_stack": {
            "terms": {"field": "stack", "size": 20}
        },
        "by_remote_type": {
            "terms": {"field": "remote_type", "size": 5}
        },
        "by_country": {
            "terms": {"field": "country", "size": 15}
        },
        "by_source": {
            "terms": {"field": "source", "size": 5}
        },
        "by_experience": {
            "terms": {"field": "experience_level", "size": 5}
        },
        "salary_histogram": {
            "histogram": {
                "field": "salary_min",
                "interval": 10000,
                "min_doc_count": 1,
            }
        },
        "salary_stats": {
            "stats": {"field": "salary_min"}
        },
    }

    # ── Highlighting ─────────────────────────────────────────────────────────
    highlight = {
        "fields": {
            "title":       {"number_of_fragments": 0},
            "description": {"number_of_fragments": 2, "fragment_size": 160},
        },
        "pre_tags":  ["<mark>"],
        "post_tags": ["</mark>"],
    }

    return {
        "from": (page - 1) * size,
        "size": size,
        "query": {
            "bool": {
                "must": must,
                "filter": filters,
            }
        },
        "sort": sort_clause,
        "aggs": aggs,
        "highlight": highlight,
        "_source": {
            "excludes": ["description"]   # exclude heavy field from list view
        },
    }


def parse_response(raw: dict, include_description: bool = False) -> dict:
    """Shape the raw OpenSearch response into a clean API response."""
    hits = raw.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    items = []

    for hit in hits.get("hits", []):
        src = hit.get("_source", {})
        item = {
            "id":               src.get("id"),
            "title":            src.get("title"),
            "company":          src.get("company"),
            "location":         src.get("location"),
            "country":          src.get("country"),
            "remote_type":      src.get("remote_type"),
            "salary_min":       src.get("salary_min"),
            "salary_max":       src.get("salary_max"),
            "salary_currency":  src.get("salary_currency"),
            "stack":            src.get("stack", []),
            "experience_level": src.get("experience_level"),
            "posted_at":        src.get("posted_at"),
            "source":           src.get("source"),
            "apply_url":        src.get("apply_url"),
            "score":            hit.get("_score"),
            "highlight":        hit.get("highlight", {}),
        }
        if include_description:
            item["description"] = src.get("description", "")
        items.append(item)

    # Shape aggregations
    raw_aggs = raw.get("aggregations", {})
    aggs = {
        "stack":        _buckets(raw_aggs, "by_stack"),
        "remote_type":  _buckets(raw_aggs, "by_remote_type"),
        "country":      _buckets(raw_aggs, "by_country"),
        "source":       _buckets(raw_aggs, "by_source"),
        "experience":   _buckets(raw_aggs, "by_experience"),
        "salary_histogram": _histogram(raw_aggs),
        "salary_stats": raw_aggs.get("salary_stats", {}),
    }

    return {"total": total, "items": items, "aggregations": aggs}


def _buckets(aggs: dict, key: str) -> list[dict]:
    return [
        {"value": b["key"], "count": b["doc_count"]}
        for b in aggs.get(key, {}).get("buckets", [])
    ]


def _histogram(aggs: dict) -> list[dict]:
    return [
        {"salary": int(b["key"]), "count": b["doc_count"]}
        for b in aggs.get("salary_histogram", {}).get("buckets", [])
        if b["doc_count"] > 0
    ]
