import pytest
from search.query_builder import build_query, parse_response


class TestBuildQuery:
    def test_empty_query_uses_match_all(self):
        body = build_query({})
        must = body["query"]["bool"]["must"]
        assert any("match_all" in clause for clause in must)

    def test_text_query_uses_multi_match(self):
        body = build_query({"q": "angular developer"})
        must = body["query"]["bool"]["must"]
        assert any("multi_match" in clause for clause in must)

    def test_multi_match_boosts_title(self):
        body = build_query({"q": "python"})
        mm = next(c["multi_match"] for c in body["query"]["bool"]["must"] if "multi_match" in c)
        title_field = next(f for f in mm["fields"] if f.startswith("title"))
        assert "^" in title_field
        boost = float(title_field.split("^")[1])
        assert boost >= 3

    def test_stack_filter_added(self):
        body = build_query({"stack": "Angular,React"})
        filters = body["query"]["bool"]["filter"]
        terms_filters = [f for f in filters if "terms" in f]
        stack_filter = next(f for f in terms_filters if "stack" in f["terms"])
        assert "Angular" in stack_filter["terms"]["stack"]
        assert "React" in stack_filter["terms"]["stack"]

    def test_salary_range_filter(self):
        body = build_query({"salary_min": "50000", "salary_max": "100000"})
        filters = body["query"]["bool"]["filter"]
        range_filter = next(f for f in filters if "range" in f)
        assert range_filter["range"]["salary_min"]["gte"] == 50000
        assert range_filter["range"]["salary_min"]["lte"] == 100000

    def test_pagination(self):
        body = build_query({"page": "3", "size": "10"})
        assert body["from"] == 20
        assert body["size"] == 10

    def test_size_capped_at_max(self):
        body = build_query({"size": "9999"})
        assert body["size"] <= 100

    def test_sort_by_date(self):
        body = build_query({"sort": "date"})
        assert any("posted_at" in str(s) for s in body["sort"])

    def test_sort_by_salary(self):
        body = build_query({"sort": "salary"})
        assert any("salary_min" in str(s) for s in body["sort"])

    def test_aggregations_always_present(self):
        body = build_query({})
        aggs = body["aggs"]
        assert "by_stack" in aggs
        assert "salary_histogram" in aggs
        assert "salary_stats" in aggs

    def test_highlighting_configured(self):
        body = build_query({"q": "python"})
        assert "highlight" in body
        assert "title" in body["highlight"]["fields"]
        assert "description" in body["highlight"]["fields"]

    def test_description_excluded_from_source(self):
        body = build_query({})
        excludes = body["_source"].get("excludes", [])
        assert "description" in excludes

    def test_multiple_filters_combined(self):
        body = build_query({"q": "backend", "stack": "Python", "remote_type": "remote", "experience": "senior"})
        filters = body["query"]["bool"]["filter"]
        assert len(filters) == 3  # stack + remote_type + experience


class TestParseResponse:
    def _make_raw(self, hits=None, aggs=None):
        return {
            "hits": {
                "total": {"value": len(hits or [])},
                "hits": hits or [],
            },
            "aggregations": aggs or {},
        }

    def test_total_extracted(self):
        raw = self._make_raw()
        result = parse_response(raw)
        assert result["total"] == 0

    def test_items_shaped_correctly(self):
        raw = self._make_raw(hits=[{
            "_source": {
                "id": "abc123", "title": "Dev", "company": "Corp",
                "stack": ["Python"], "remote_type": "remote",
                "salary_min": 60000, "salary_max": 80000, "salary_currency": "GBP",
                "source": "adzuna", "apply_url": "https://example.com",
            },
            "_score": 1.5,
            "highlight": {"title": ["<mark>Dev</mark>"]},
        }])
        result = parse_response(raw)
        item = result["items"][0]
        assert item["title"] == "Dev"
        assert item["score"] == 1.5
        assert item["highlight"]["title"] == ["<mark>Dev</mark>"]
        # description excluded by default
        assert "description" not in item

    def test_stack_aggregation_shaped(self):
        raw = self._make_raw(aggs={
            "by_stack": {"buckets": [{"key": "Python", "doc_count": 42}]}
        })
        result = parse_response(raw)
        assert result["aggregations"]["stack"] == [{"value": "Python", "count": 42}]

    def test_empty_salary_histogram_excluded(self):
        raw = self._make_raw(aggs={
            "salary_histogram": {
                "buckets": [
                    {"key": 50000, "doc_count": 5},
                    {"key": 60000, "doc_count": 0},  # should be excluded
                ]
            }
        })
        histogram = parse_response(raw)["aggregations"]["salary_histogram"]
        assert all(b["count"] > 0 for b in histogram)
        assert len(histogram) == 1
