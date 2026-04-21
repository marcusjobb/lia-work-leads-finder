import logging
from datetime import date

from pipeline.enrichment.company_api import CompanyApiData, fetch_company

logger = logging.getLogger(__name__)

_TODAY_YEAR = date.today().year


def _age_score(registration_date: str) -> float:
    try:
        year = int(registration_date[:4])
    except (ValueError, TypeError):
        return 50.0
    age = _TODAY_YEAR - year
    if age >= 10:
        return 100.0
    if age >= 5:
        return 75.0
    if age >= 2:
        return 50.0
    return 20.0


async def score_stability(company_name: str, city: str) -> float:
    """Return 0–100 stability score using foretagsapi + bolagsapi (SQLite-cached)."""
    try:
        data: CompanyApiData = await fetch_company(company_name, city)
    except Exception as exc:
        logger.warning("company_api failed for %s: %s", company_name, exc)
        return 50.0

    # Inactive / deregistered company → very low score
    if not data.is_active:
        return 10.0

    # Paid tier: composite financial health score
    if data.composite_score is not None:
        return round(data.composite_score, 2)

    # Free tier: combine age + employee size (equal weight)
    scores = []
    if data.registration_date:
        scores.append(_age_score(data.registration_date))
    if data.employee_score is not None:
        scores.append(data.employee_score)

    if scores:
        return round(sum(scores) / len(scores), 2)

    return 50.0
