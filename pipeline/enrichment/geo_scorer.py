def score_geo(company_city: str, target_city: str, all_sweden: bool) -> float:
    """Return 0–100 geographic score.

    Args:
        company_city: The company's location string.
        target_city: The target city the student wants.
        all_sweden: If True, returns partial credit (60.0) for any Swedish company.

    Returns:
        Score from 0 to 100:
        - 100.0 if target city is found in company city string (case-insensitive)
        - 60.0 if all_sweden is True (partial credit for any Sweden location)
        - 30.0 otherwise (different city)
    """
    if all_sweden:
        return 60.0

    c = company_city.lower()
    t = target_city.lower()

    if t in c or c in t:
        return 100.0

    return 30.0
