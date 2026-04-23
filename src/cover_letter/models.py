from pydantic import BaseModel


class StudentProfile(BaseModel):
    name: str
    education: str
    tech_stack: list[str]
    experience: str
    languages: list[str]
    portfolio_url: str | None = None
    program_url: str | None = None
    bio: str
    lia_period: str | None = None  # t.ex. "mars–maj 2026" eller "hösten 2026"


class CompanyResearch(BaseModel):
    company_name: str
    website: str | None
    about_text: str
    values: list[str]
    recent_news: list[str]
    detected_language: str  # "svenska" or "engelska"
