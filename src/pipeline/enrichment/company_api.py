"""Fetches company data from foretagsapi.se and bolagsapi.se with SQLite caching."""
import logging
import os
from dataclasses import dataclass

import httpx

from pipeline.enrichment.company_cache import get, put

logger = logging.getLogger(__name__)

_FORETAGSAPI_URL = "https://data.foretagsapi.se/v1/search"
_BOLAGSAPI_URL   = "https://api.bolagsapi.se/v1/company"


@dataclass
class CompanyApiData:
    org_number: str | None = None
    registration_date: str | None = None   # "YYYY-MM-DD"
    is_active: bool = True
    business_description: str | None = None
    # From bolagsapi free tier
    employee_score: float | None = None    # derived from size.employees
    # From bolagsapi paid tier
    composite_score: float | None = None   # 0–100 financial health
    website: str | None = None
    linkedin: str | None = None


async def fetch_company(company_name: str, city: str) -> CompanyApiData:
    """Return cached-or-fetched company data. Always returns something (never raises)."""
    cached = get(company_name, city)
    if cached:
        return _parse(cached["foretagsapi"], cached["bolagsapi"])

    foretagsapi_data = await _fetch_foretagsapi(company_name, city)
    org_number = foretagsapi_data.get("orgNumber") if foretagsapi_data else None

    bolagsapi_data = None
    if org_number:
        bolagsapi_data = await _fetch_bolagsapi(org_number)

    put(company_name, city, org_number, foretagsapi_data, bolagsapi_data)
    return _parse(foretagsapi_data, bolagsapi_data)


_EMP_RANGE_SCORE = {
    "1-4":    20.0,
    "5-19":   60.0,
    "20-49":  85.0,
    "50-249": 95.0,
}


def _parse_employee_score(size: dict | None) -> float | None:
    if not size or not isinstance(size, dict):
        return None
    emp = size.get("employees", "")
    if not emp:
        return None
    for prefix, score in _EMP_RANGE_SCORE.items():
        if emp.startswith(prefix):
            return score
    if "250" in emp or "500" in emp or "1000" in emp:
        return 100.0
    return None


def _parse(fg: dict | None, bg: dict | None) -> CompanyApiData:
    data = CompanyApiData()
    if fg:
        data.org_number = fg.get("orgNumber")
        data.registration_date = fg.get("registrationDate")
        data.is_active = fg.get("ftgstat", 1) == 1 and fg.get("deregistrationDate") is None
        data.business_description = fg.get("businessDescription")
    if bg:
        fh = bg.get("financial_health") or {}
        # composite_score only on paid tier — check it's a real number
        cs = fh.get("composite_score")
        data.composite_score = cs if isinstance(cs, (int, float)) else None

        # employee size available on free tier
        data.employee_score = _parse_employee_score(bg.get("size"))

        # website/linkedin on paid tier
        data.website = bg.get("website") or None
        data.linkedin = bg.get("linkedin") or None

        if not data.registration_date:
            data.registration_date = bg.get("registered_date")
    return data


async def _fetch_foretagsapi(company_name: str, city: str) -> dict | None:
    key = os.getenv("FORETAGSAPI_KEY", "")
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    payload = {"q": f"{company_name} {city}", "limit": 3}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.post(_FORETAGSAPI_URL, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        companies = data.get("companies", [])
        if not companies:
            return None
        # Take highest-scoring result that matches city
        city_l = city.lower()
        for c in companies:
            if city_l in (c.get("postalAddress") or {}).get("city", "").lower():
                return c
        return companies[0]  # fallback: best match regardless of city
    except Exception as exc:
        logger.warning("foretagsapi failed for %s: %s", company_name, exc)
        return None


async def _fetch_bolagsapi(org_number: str) -> dict | None:
    key = os.getenv("BOLAGSAPI_KEY", "")
    if not key:
        return None
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                f"{_BOLAGSAPI_URL}/{org_number}",
                headers={"Authorization": f"Bearer {key}"},
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        logger.warning("bolagsapi failed for %s: %s", org_number, exc)
        return None
