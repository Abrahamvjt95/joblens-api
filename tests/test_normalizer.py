import pytest
from normalizer.handler import normalize_batch, _normalize_adzuna, _normalize_themuse, _normalize_remotive, _normalize_arbeitnow


def adzuna_job(**kwargs):
    base = {
        "id": "az123",
        "title": "Senior Angular Developer",
        "company": {"display_name": "TechCorp"},
        "description": "We use Angular TypeScript and Node.js. Fully remote.",
        "location": {"display_name": "London"},
        "country": "gb",
        "salary_min": 70000,
        "salary_max": 90000,
        "redirect_url": "https://adzuna.com/jobs/az123",
        "created": "2026-05-13T09:00:00Z",
    }
    return {**base, **kwargs}


def remotive_job(**kwargs):
    base = {
        "id": "rm456",
        "title": "Python Backend Developer",
        "company_name": "RemoteCo",
        "description": "Django REST framework, PostgreSQL, Docker. Remote worldwide.",
        "candidate_required_location": "Worldwide",
        "url": "https://remotive.com/jobs/rm456",
        "salary": "$80,000 - $110,000",
        "publication_date": "2026-05-12",
        "tags": ["python", "django", "postgresql"],
    }
    return {**base, **kwargs}


class TestNormalizeAdzuna:
    def test_basic_normalization(self):
        job = _normalize_adzuna(adzuna_job())
        assert job is not None
        assert job.title == "Senior Angular Developer"
        assert job.company == "TechCorp"
        assert job.salary_min == 70000
        assert job.salary_max == 90000
        assert job.salary_currency == "GBP"
        assert job.source == "adzuna"
        assert job.experience_level == "senior"

    def test_stack_extracted_from_description(self):
        job = _normalize_adzuna(adzuna_job())
        assert "Angular" in job.stack
        assert "TypeScript" in job.stack
        assert "Node.js" in job.stack

    def test_remote_type_inferred(self):
        job = _normalize_adzuna(adzuna_job())
        assert job.remote_type == "remote"

    def test_returns_none_on_exception(self):
        # Pass completely broken data
        result = _normalize_adzuna({"company": None, "title": None})
        assert result is None


class TestNormalizeRemotive:
    def test_basic_normalization(self):
        job = _normalize_remotive(remotive_job())
        assert job is not None
        assert job.title == "Python Backend Developer"
        assert job.remote_type == "remote"
        assert job.salary_min == 80000
        assert job.salary_max == 110000
        assert job.salary_currency == "USD"

    def test_tags_merged_into_stack(self):
        job = _normalize_remotive(remotive_job())
        assert "Python" in job.stack
        assert "Django" in job.stack
        assert "PostgreSQL" in job.stack

    def test_posted_at_truncated_to_date(self):
        job = _normalize_remotive(remotive_job())
        assert job.posted_at == "2026-05-12"


class TestNormalizeBatch:
    def test_deduplication_within_batch(self):
        raw = [adzuna_job(), adzuna_job()]  # same job twice
        result = normalize_batch("adzuna", raw)
        assert len(result) == 1

    def test_failed_jobs_are_skipped(self):
        raw = [adzuna_job(), {"bad": "data", "company": None}]
        result = normalize_batch("adzuna", raw)
        assert len(result) == 1  # only the valid one

    def test_unknown_source_raises(self):
        with pytest.raises(ValueError, match="Unknown source"):
            normalize_batch("unknown_source", [])

    def test_result_contains_expected_fields(self):
        result = normalize_batch("adzuna", [adzuna_job()])
        job = result[0]
        for field in ["id", "title", "company", "stack", "source", "remote_type"]:
            assert field in job

    def test_remotive_batch(self):
        result = normalize_batch("remotive", [remotive_job()])
        assert len(result) == 1
        assert result[0]["source"] == "remotive"
