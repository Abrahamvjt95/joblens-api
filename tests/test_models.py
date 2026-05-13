import pytest
from shared.models import JobListing


def make_job(**kwargs) -> JobListing:
    defaults = dict(
        title="Software Engineer",
        company="Acme Corp",
        description="Build great software",
        source="adzuna",
        apply_url="https://example.com/apply",
    )
    return JobListing(**{**defaults, **kwargs})


class TestJobListingId:
    def test_id_is_deterministic(self):
        j1 = make_job()
        j2 = make_job()
        assert j1.id == j2.id

    def test_different_titles_produce_different_ids(self):
        j1 = make_job(title="Backend Developer")
        j2 = make_job(title="Frontend Developer")
        assert j1.id != j2.id

    def test_id_is_16_chars(self):
        assert len(make_job().id) == 16

    def test_id_ignores_case_and_whitespace(self):
        j1 = make_job(title="  senior developer  ", company="acme")
        j2 = make_job(title="SENIOR DEVELOPER", company="ACME")
        assert j1.id == j2.id


class TestJobListingToDict:
    def test_to_dict_contains_required_fields(self):
        d = make_job().to_dict()
        for field in ["id", "title", "company", "description", "source", "apply_url"]:
            assert field in d

    def test_stack_is_deduplicated_and_sorted(self):
        job = make_job(stack=["Python", "python", "Angular", "angular"])
        d = job.to_dict()
        assert d["stack"] == ["angular", "python"]

    def test_stack_is_lowercased(self):
        job = make_job(stack=["Angular", "TypeScript"])
        d = job.to_dict()
        assert all(s == s.lower() for s in d["stack"])


class TestJobListingFromDict:
    def test_roundtrip(self):
        original = make_job(stack=["Angular"], salary_min=60000, experience_level="senior")
        restored = JobListing.from_dict(original.to_dict())
        assert restored.title == original.title
        assert restored.company == original.company
        assert restored.salary_min == original.salary_min

    def test_from_dict_ignores_id_field(self):
        d = make_job().to_dict()
        d["id"] = "should_be_ignored"
        job = JobListing.from_dict(d)
        # id is recomputed in __post_init__
        assert job.id != "should_be_ignored"
