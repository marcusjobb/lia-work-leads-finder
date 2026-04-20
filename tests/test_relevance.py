from models import ContactInfo, LeadProfile, ScoreBreakdown
from pipeline.validators.relevance import is_relevant
from quality_gate import compute_score, assign_tier


def _make_profile(tech_score: float) -> LeadProfile:
    bd = ScoreBreakdown(
        tech_match=tech_score, geo=100, contact=0, activity=80, stability=50
    )
    score = compute_score(bd)
    return LeadProfile(
        company_name="Test AB",
        city="Göteborg",
        tech_tags=[],
        contact=ContactInfo(),
        score=score,
        score_breakdown=bd,
        match_reason="test",
        tier=assign_tier(score),
    )


def test_high_tech_score_is_relevant():
    assert is_relevant(_make_profile(70)) is True


def test_zero_tech_score_is_not_relevant():
    assert is_relevant(_make_profile(0)) is False


def test_threshold_boundary():
    # Profiles with tech_score >= 10 are relevant
    assert is_relevant(_make_profile(10)) is True
    assert is_relevant(_make_profile(9)) is False
