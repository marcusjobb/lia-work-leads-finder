from datetime import date

_MAX_DAYS = 180  # 6 months = 0 points


def score_activity(publication_date: str | None) -> float:
    """Return 0–100 linearly. Today=100, 6 months ago=0, older/unknown=0."""
    if not publication_date:
        return 0.0
    try:
        pub_date = date.fromisoformat(publication_date[:10])
    except (ValueError, TypeError):
        return 0.0
    delta = (date.today() - pub_date).days
    return max(0.0, round(100.0 - delta / _MAX_DAYS * 100, 2))
