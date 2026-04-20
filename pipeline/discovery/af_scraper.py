import logging

import httpx

from models import CompanyRaw

logger = logging.getLogger(__name__)

AF_SEARCH_URL = "https://jobsearch.api.jobtechdev.se/search"
HEADERS = {"Accept": "application/json"}


async def scrape_af(
    tech_stack: list[str], city: str, all_sweden: bool = False
) -> list[CompanyRaw]:
    """Search Arbetsförmedlingen JobSearch API → list[CompanyRaw]. Returns [] on error."""
    query_parts = tech_stack[:3]
    if not all_sweden:
        query_parts = query_parts + [city]

    params = {
        "q": " ".join(query_parts),
        "limit": 20,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(AF_SEARCH_URL, params=params, headers=HEADERS)
            response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logger.warning("AF scrape failed: %s", exc)
        return []

    try:
        companies: list[CompanyRaw] = []
        for hit in data.get("hits", []):
            employer = hit.get("employer") or {}
            address = hit.get("workplace_address") or {}
            name = employer.get("name", "").strip()
            if not name:
                continue
            companies.append(
                CompanyRaw(
                    name=name,
                    city=address.get("city") or address.get("municipality") or city,
                    source="af",
                    job_title=hit.get("headline"),
                    job_url=hit.get("webpage_url"),
                )
            )
        return companies
    except Exception as exc:
        logger.warning("AF parse failed: %s", exc)
        return []
