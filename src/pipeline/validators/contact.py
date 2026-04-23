from models import LeadProfile


def is_reachable(profile: LeadProfile) -> bool:
    """True if there is at least one way to contact the company."""
    c = profile.contact
    return bool(c.email or c.contact_url or c.careers_page or c.linkedin_url or profile.website or profile.job_url)
