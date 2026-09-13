from models import ScoreBreakdown
from pipeline.quality_gate import compute_score, assign_tier, WEIGHTS


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 0.001


def test_compute_score_perfect():
    bd = ScoreBreakdown(tech_match=100, geo=100, contact=100, activity=100, stability=100, seniority=100)
    assert compute_score(bd) == 100.0


def test_compute_score_weighted():
    bd = ScoreBreakdown(tech_match=100, geo=0, contact=0, activity=0, stability=0, seniority=0)
    # Only tech_match (30%) contributes
    assert abs(compute_score(bd) - 30.0) < 0.01


def test_compute_score_geo_contributes():
    bd = ScoreBreakdown(tech_match=0, geo=100, contact=0, activity=0, stability=0, seniority=0)
    # Only geo (25%) contributes
    assert abs(compute_score(bd) - 25.0) < 0.01


def test_assign_tier():
    assert assign_tier(75) == "STRONG"
    assert assign_tier(60) == "GOOD"
    assert assign_tier(40) == "WEAK"
    assert assign_tier(20) == "SKIP"
