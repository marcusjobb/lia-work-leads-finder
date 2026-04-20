from models import ScoreBreakdown

WEIGHTS = {
    "tech_match": 0.30,
    "geo": 0.25,
    "contact": 0.20,
    "activity": 0.15,
    "stability": 0.10,
}


def compute_score(breakdown: ScoreBreakdown) -> float:
    return round(
        breakdown.tech_match * WEIGHTS["tech_match"]
        + breakdown.geo * WEIGHTS["geo"]
        + breakdown.contact * WEIGHTS["contact"]
        + breakdown.activity * WEIGHTS["activity"]
        + breakdown.stability * WEIGHTS["stability"],
        2,
    )


def assign_tier(score: float) -> str:
    if score >= 70:
        return "STRONG"
    if score >= 50:
        return "GOOD"
    if score >= 30:
        return "WEAK"
    return "SKIP"
