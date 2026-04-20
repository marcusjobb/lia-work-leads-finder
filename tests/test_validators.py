from models import CompanyRaw, ContactInfo, LeadProfile, ScoreBreakdown, SearchConfig
from pipeline.validators.completeness import is_complete
from pipeline.validators.contact import is_reachable
from pipeline.integration import build_profile


def _profile(**kwargs) -> LeadProfile:
    defaults = dict(
        company_name="Test AB", city="Göteborg", source="af",
        tech_tags=[], contact=ContactInfo(),
        score=50.0,
        score_breakdown=ScoreBreakdown(
            tech_match=50, geo=50, contact=0, activity=50, stability=50, seniority=50
        ),
        match_reason="test", tier="GOOD",
    )
    defaults.update(kwargs)
    return LeadProfile(**defaults)


def test_complete_with_name_and_city():
    assert is_complete(_profile()) is True


def test_incomplete_missing_city():
    p = _profile()
    p.city = ""
    assert is_complete(p) is False


def test_reachable_via_email():
    assert is_reachable(_profile(contact=ContactInfo(email="hr@test.se"))) is True


def test_reachable_via_contact_url():
    assert is_reachable(_profile(contact=ContactInfo(contact_url="https://test.se/kontakt"))) is True


def test_reachable_via_website():
    assert is_reachable(_profile(website="https://test.se")) is True


def test_reachable_via_job_url():
    assert is_reachable(_profile(job_url="https://af.se/job/1")) is True


def test_not_reachable_no_contact():
    assert is_reachable(_profile()) is False
