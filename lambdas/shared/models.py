from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import date
import hashlib
import json


@dataclass
class JobListing:
    title: str
    company: str
    description: str
    source: str
    apply_url: str
    location: str = ""
    country: str = ""
    remote_type: str = "onsite"        # remote | hybrid | onsite
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None
    stack: list = field(default_factory=list)
    experience_level: Optional[str] = None  # junior | mid | senior
    posted_at: Optional[str] = None         # ISO date string YYYY-MM-DD
    id: str = field(init=False)

    def __post_init__(self):
        self.id = self._generate_id()
        if self.posted_at is None:
            self.posted_at = date.today().isoformat()

    def _generate_id(self) -> str:
        raw = f"{self.company.lower().strip()}|{self.title.lower().strip()}|{self.location.lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def to_dict(self) -> dict:
        d = asdict(self)
        # keep stack as list of lowercase strings, deduplicated
        d["stack"] = sorted(set(s.lower() for s in d["stack"]))
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "JobListing":
        data.pop("id", None)
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
