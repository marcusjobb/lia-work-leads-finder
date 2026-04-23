from models import LeadProfile

TECH_SCORE_MINIMUM = 10.0


def is_relevant(profile: LeadProfile) -> bool:
    """True if tech match is above minimum threshold."""
    return profile.score_breakdown.tech_match >= TECH_SCORE_MINIMUM
