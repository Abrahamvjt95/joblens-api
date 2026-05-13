from __future__ import annotations
import re
from typing import Optional

# Canonical tech keywords → normalized label
# Order matters: longer/more specific first to avoid partial matches
TECH_PATTERNS: list[tuple[str, str]] = [
    # Frontend
    (r"\bangular\b", "Angular"),
    (r"\breact\s*(?:\.js|js)?\b", "React"),
    (r"\bvue\s*(?:\.js|js)?\b", "Vue"),
    (r"\bnext\s*\.js\b", "Next.js"),
    (r"\bnuxt\b", "Nuxt"),
    (r"\bsvelte\b", "Svelte"),
    (r"\btypescript\b", "TypeScript"),
    (r"\bjavascript\b|\bjs\b", "JavaScript"),
    (r"\brxjs\b", "RxJS"),
    (r"\bhtml5?\b", "HTML"),
    (r"\bcss3?\b", "CSS"),
    (r"\bsass\b|\bscss\b", "SCSS"),
    (r"\btailwind\b", "Tailwind"),
    # Backend
    (r"\bnode\s*(?:\.js|js)?\b", "Node.js"),
    (r"\bexpress\s*(?:\.js|js)?\b", "Express"),
    (r"\bnestjs\b|\bnest\.js\b", "NestJS"),
    (r"\bdjango\b", "Django"),
    (r"\bfastapi\b", "FastAPI"),
    (r"\bflask\b", "Flask"),
    (r"\bspring\s*boot\b", "Spring Boot"),
    (r"\bspring\b", "Spring"),
    (r"\bjava\b", "Java"),
    (r"\bkotlin\b", "Kotlin"),
    (r"\bscala\b", "Scala"),
    (r"\bpython\b", "Python"),
    (r"\bruby\s*on\s*rails\b|\brails\b", "Ruby on Rails"),
    (r"\bruby\b", "Ruby"),
    (r"\bphp\b", "PHP"),
    (r"\blaravel\b", "Laravel"),
    (r"\bgo\b|\bgolang\b", "Go"),
    (r"\brust\b", "Rust"),
    (r"\b\.net\b|\bdotnet\b", ".NET"),
    (r"\bc#\b|\bcsharp\b", "C#"),
    (r"\bc\+\+\b", "C++"),
    # Databases
    (r"\bpostgresql\b|\bpostgres\b", "PostgreSQL"),
    (r"\bmysql\b", "MySQL"),
    (r"\bmongodb\b|\bmongo\b", "MongoDB"),
    (r"\bredis\b", "Redis"),
    (r"\belasticsearch\b", "Elasticsearch"),
    (r"\bopensearch\b", "OpenSearch"),
    (r"\bdynamodb\b", "DynamoDB"),
    (r"\bcassandra\b", "Cassandra"),
    (r"\bsqlite\b", "SQLite"),
    # Cloud & DevOps
    (r"\baws\b|amazon\s+web\s+services", "AWS"),
    (r"\blambda\b", "AWS Lambda"),
    (r"\bs3\b", "S3"),
    (r"\bec2\b", "EC2"),
    (r"\beks\b", "EKS"),
    (r"\bgcp\b|google\s+cloud", "GCP"),
    (r"\bazure\b", "Azure"),
    (r"\bdocker\b", "Docker"),
    (r"\bkubernetes\b|\bk8s\b", "Kubernetes"),
    (r"\bterraform\b", "Terraform"),
    (r"\bansible\b", "Ansible"),
    (r"\bjenkins\b", "Jenkins"),
    (r"\bgithub\s+actions\b", "GitHub Actions"),
    (r"\bci\s*/\s*cd\b|\bcicd\b", "CI/CD"),
    # Data & ML
    (r"\bkafka\b", "Kafka"),
    (r"\brabbitmq\b", "RabbitMQ"),
    (r"\bspark\b", "Apache Spark"),
    (r"\bairflow\b", "Airflow"),
    (r"\btensorflow\b", "TensorFlow"),
    (r"\bpytorch\b", "PyTorch"),
    (r"\bpandas\b", "Pandas"),
    # Mobile
    (r"\bflutter\b", "Flutter"),
    (r"\breact\s+native\b", "React Native"),
    (r"\bswift\b", "Swift"),
    (r"\bandroid\b", "Android"),
    (r"\bios\b", "iOS"),
    # Testing
    (r"\bjest\b", "Jest"),
    (r"\bcypress\b", "Cypress"),
    (r"\bselenium\b", "Selenium"),
    (r"\bjunit\b", "JUnit"),
    (r"\bpytest\b", "pytest"),
]

# Compiled once at module load
_COMPILED = [(re.compile(pattern, re.IGNORECASE), label) for pattern, label in TECH_PATTERNS]


def extract_stack(text: str, existing_tags: list[str] | None = None) -> list[str]:
    """
    Extract tech stack from free-form text and merge with existing tags.
    Returns deduplicated, sorted list of canonical tech names.
    """
    found: set[str] = set()

    # Start with any explicit tags provided by the API
    if existing_tags:
        tag_text = " ".join(existing_tags)
        for pattern, label in _COMPILED:
            if pattern.search(tag_text):
                found.add(label)

    # Scan the description
    for pattern, label in _COMPILED:
        if pattern.search(text):
            found.add(label)

    return sorted(found)


def infer_experience_level(text: str) -> Optional[str]:
    """Infer seniority from job title or description."""
    t = text.lower()
    if any(w in t for w in ["senior", "sr.", "lead", "principal", "staff", "architect"]):
        return "senior"
    if any(w in t for w in ["junior", "jr.", "graduate", "entry", "intern", "trainee"]):
        return "junior"
    if any(w in t for w in ["mid", "middle", "intermediate", "ii ", " ii)", "iii "]):
        return "mid"
    return None


def infer_remote_type(text: str) -> str:
    """Infer remote/hybrid/onsite from job description."""
    t = text.lower()
    if "fully remote" in t or "100% remote" in t or "remote only" in t:
        return "remote"
    if "remote" in t and ("hybrid" in t or "occasional" in t or "flexible" in t):
        return "hybrid"
    if "remote" in t:
        return "remote"
    if "hybrid" in t:
        return "hybrid"
    return "onsite"
