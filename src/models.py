from typing import Literal
from pydantic import BaseModel, Field, field_validator


class SearchConfig(BaseModel):
    city: str = ""
    tech_stack: list[str]
    all_sweden: bool = False
    program_url: str | None = None
    radius_km: int = 0
    page: int = 1
    page_size: int = 10


class CompanyRaw(BaseModel):
    name: str
    website: str | None = None
    city: str
    source: str
    job_title: str | None = None
    job_url: str | None = None
    description: str | None = None  # raw text for tech analysis
    publication_date: str | None = None  # ISO 8601 from job board API


class ContactInfo(BaseModel):
    email: str | None = None
    contact_url: str | None = None
    linkedin_url: str | None = None
    careers_page: str | None = None


class ScoreBreakdown(BaseModel):
    tech_match: float
    geo: float
    contact: float
    activity: float
    stability: float
    seniority: float

    @field_validator("tech_match", "geo", "contact", "activity", "stability", "seniority")
    @classmethod
    def must_be_0_to_100(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError(f"Score must be 0–100, got {v}")
        return v


class LeadProfile(BaseModel):
    company_name: str
    org_number: str | None = None
    website: str | None = None
    city: str
    source: str = "unknown"
    job_title: str | None = None
    job_url: str | None = None
    publication_date: str | None = None
    tech_tags: list[str]
    contact: ContactInfo
    score: float = Field(ge=0.0, le=100.0)
    score_breakdown: ScoreBreakdown
    match_reason: str
    tier: Literal["STRONG", "GOOD", "WEAK", "SKIP"]
    # Stability context (populated after API enrichment)
    registration_date: str | None = None
    employee_range: str | None = None
    is_active: bool | None = None
