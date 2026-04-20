import logging

import httpx

from models import CompanyRaw

logger = logging.getLogger(__name__)

AF_SEARCH_URL = "https://jobsearch.api.jobtechdev.se/search"
HEADERS = {"Accept": "application/json"}
PAGE_SIZE = 10


async def scrape_af(
    tech_stack: list[str], city: str, all_sweden: bool = False, page: int = 1
) -> tuple[list[CompanyRaw], int]:
    """Search Arbetsförmedlingen JobSearch API. Returns (companies, total_hits)."""
    query_parts = tech_stack[:3]
    if not all_sweden:
        query_parts = query_parts + [city]

    params = {
        "q": " ".join(query_parts),
        "offset": (page - 1) * PAGE_SIZE,
        "limit": PAGE_SIZE,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(AF_SEARCH_URL, params=params, headers=HEADERS)
            response.raise_for_status()
            data = response.json()
    except Exception as exc:
        logger.warning("AF scrape failed: %s", exc)
        return [], 0

    total = data.get("total", {}).get("value", 0)

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
                    publication_date=hit.get("publication_date"),
                )
            )
        return companies, total
    except Exception as exc:
        logger.warning("AF parse failed: %s", exc)
        return [], 0
