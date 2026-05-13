import pytest
from normalizer.stack_extractor import extract_stack, infer_experience_level, infer_remote_type


class TestExtractStack:
    def test_detects_angular_in_title(self):
        result = extract_stack("Senior Angular Developer")
        assert "Angular" in result

    def test_detects_multiple_technologies(self):
        text = "We need Node.js, TypeScript, PostgreSQL and Docker experience"
        result = extract_stack(text)
        assert "Node.js" in result
        assert "TypeScript" in result
        assert "PostgreSQL" in result
        assert "Docker" in result

    def test_case_insensitive(self):
        result = extract_stack("ANGULAR TYPESCRIPT REACT")
        assert "Angular" in result
        assert "TypeScript" in result
        assert "React" in result

    def test_existing_tags_merged(self):
        result = extract_stack("backend position", existing_tags=["python", "django"])
        assert "Python" in result
        assert "Django" in result

    def test_returns_sorted_deduplicated_list(self):
        result = extract_stack("angular angular angular")
        assert result.count("Angular") == 1
        assert result == sorted(result)

    def test_spring_boot_detected(self):
        result = extract_stack("Spring Boot microservices")
        assert "Spring Boot" in result

    def test_detects_aws_services(self):
        text = "Experience with AWS Lambda, S3 and API Gateway"
        result = extract_stack(text)
        assert "AWS" in result
        assert "AWS Lambda" in result
        assert "S3" in result

    def test_empty_text_returns_empty(self):
        assert extract_stack("") == []

    def test_react_native_not_confused_with_react(self):
        result = extract_stack("React Native mobile developer")
        assert "React Native" in result

    def test_nextjs_detected(self):
        result = extract_stack("Next.js full stack developer")
        assert "Next.js" in result


class TestInferExperienceLevel:
    def test_senior_titles(self):
        assert infer_experience_level("Senior Software Engineer") == "senior"
        assert infer_experience_level("Lead Developer") == "senior"
        assert infer_experience_level("Principal Architect") == "senior"

    def test_junior_titles(self):
        assert infer_experience_level("Junior Angular Developer") == "junior"
        assert infer_experience_level("Graduate Software Engineer") == "junior"

    def test_mid_titles(self):
        assert infer_experience_level("Mid-level Python Developer") == "mid"

    def test_unknown_returns_none(self):
        assert infer_experience_level("Software Engineer") is None

    def test_case_insensitive(self):
        assert infer_experience_level("SENIOR DEVELOPER") == "senior"


class TestInferRemoteType:
    def test_fully_remote(self):
        assert infer_remote_type("Fully remote position") == "remote"
        assert infer_remote_type("100% remote, work from anywhere") == "remote"

    def test_hybrid(self):
        assert infer_remote_type("Hybrid role, remote and office") == "hybrid"

    def test_remote_without_qualifier(self):
        assert infer_remote_type("This role can be done remote") == "remote"

    def test_onsite_default(self):
        assert infer_remote_type("Office based in Lisbon") == "onsite"

    def test_case_insensitive(self):
        assert infer_remote_type("FULLY REMOTE") == "remote"
