import pytest
from pydantic import ValidationError
from models import SearchConfig, CompanyRaw, LeadProfile, ScoreBreakdown, ContactInfo


def test_search_config_defaults():
    cfg = SearchConfig(city="Göteborg", tech_stack=["Java"])
    assert cfg.all_sweden is False
    assert cfg.program_url is None


def test_lead_profile_tier_field():
    profile = LeadProfile(
        company_name="Acme AB",
        city="Göteborg",
        tech_tags=["java"],
        contact=ContactInfo(),
        score=75.0,
        score_breakdown=ScoreBreakdown(
            tech_match=80, geo=100, contact=0, activity=80, stability=50, seniority=50
        ),
        match_reason="Matchar Java, Göteborg",
        tier="STRONG",
    )
    assert profile.tier == "STRONG"


def test_company_raw_optional_fields():
    c = CompanyRaw(name="Foo AB", city="Stockholm", source="indeed")
    assert c.website is None
    assert c.job_title is None


def test_score_breakdown_rejects_out_of_range():
    with pytest.raises(ValidationError):
        ScoreBreakdown(tech_match=150, geo=100, contact=0, activity=80, stability=50, seniority=50)


def test_score_breakdown_accepts_valid_scores():
    breakdown = ScoreBreakdown(tech_match=85, geo=100, contact=0, activity=80, stability=50, seniority=50)
    assert breakdown.tech_match == 85
    assert breakdown.geo == 100
    assert breakdown.contact == 0
    assert breakdown.activity == 80
    assert breakdown.stability == 50


def test_lead_profile_score_must_be_0_to_100():
    with pytest.raises(ValidationError):
        LeadProfile(
            company_name="Test Corp",
            city="Stockholm",
            tech_tags=["Python"],
            contact=ContactInfo(),
            score=150,
            score_breakdown=ScoreBreakdown(tech_match=80, geo=70, contact=60, activity=50, stability=40, seniority=50),
            match_reason="High tech match",
            tier="STRONG"
        )


def test_lead_profile_score_accepts_valid_range():
    profile = LeadProfile(
        company_name="Test Corp",
        city="Stockholm",
        tech_tags=["Python"],
        contact=ContactInfo(),
        score=75,
        score_breakdown=ScoreBreakdown(tech_match=80, geo=70, contact=60, activity=50, stability=40, seniority=50),
        match_reason="High tech match",
        tier="STRONG"
    )
    assert profile.score == 75
