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
            tech_match=80, geo=100, contact=0, activity=80, stability=50
        ),
        match_reason="Matchar Java, Göteborg",
        tier="STRONG",
    )
    assert profile.tier == "STRONG"


def test_company_raw_optional_fields():
    c = CompanyRaw(name="Foo AB", city="Stockholm", source="indeed")
    assert c.website is None
    assert c.job_title is None
