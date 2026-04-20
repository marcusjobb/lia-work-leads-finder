from models import LeadProfile


def is_complete(profile: LeadProfile) -> bool:
    """True if profile has the minimum fields needed to be actionable."""
    return bool(profile.company_name and profile.city)
