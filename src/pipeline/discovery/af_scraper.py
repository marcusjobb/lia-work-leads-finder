import logging
from itertools import combinations

import httpx

from models import CompanyRaw
from pipeline.enrichment.geocoder import geocode

logger = logging.getLogger(__name__)

AF_SEARCH_URL = "https://jobsearch.api.jobtechdev.se/search"
HEADERS = {"Accept": "application/json"}
PAGE_SIZE = 10


def _candidate_query_sets(query_parts: list[str]) -> list[list[str]]:
    """Full term set first, then progressively smaller subsets.

    A single rare/narrow term (e.g. a long Swedish compound word AF's search
    doesn't decompose, like "Yrkeshögskolelärare") can silently zero out an
    otherwise good combined query. Subsets are tried dropping one term at a
    time (favoring dropping the last term first), then down to each term
    alone, so scrape_af can fall back instead of just returning nothing.
    """
    n = len(query_parts)
    if n == 0:
        return [[]]
    candidates = [list(query_parts)]
    for size in range(n - 1, 0, -1):
        for combo in combinations(range(n), size):
            candidates.append([query_parts[i] for i in combo])
    return candidates


async def scrape_af(
    tech_stack: list[str], city: str, all_sweden: bool = False,
    radius_km: int = 0, limit: int = 100,
) -> tuple[list[CompanyRaw], int]:
    """Search Arbetsförmedlingen JobSearch API. Returns (companies, total_hits).

    Falls back to smaller subsets of the search terms if the full
    combination returns zero hits (see _candidate_query_sets)."""
    query_parts = tech_stack[:3]

    last_result: tuple[list[CompanyRaw], int] = ([], 0)
    for candidate in _candidate_query_sets(query_parts):
        companies, total = await _search_af(candidate, city, all_sweden, radius_km, limit)
        last_result = (companies, total)
        if total > 0:
            return companies, total
    return last_result


async def _search_af(
    query_parts: list[str], city: str, all_sweden: bool, radius_km: int, limit: int,
) -> tuple[list[CompanyRaw], int]:
    """One AF search attempt for the given query terms."""
    params: dict = {
        "q": " ".join(query_parts),
        "offset": 0,
        "limit": min(limit, 100),
    }

    if radius_km > 0:
        coords = await geocode(city)
        if coords:
            params["position"] = f"{coords[0]},{coords[1]}"
            params["position.radius"] = radius_km
        else:
            if not all_sweden:
                params["q"] += f" {city}"
    elif not all_sweden:
        params["q"] += f" {city}"

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
            desc = (hit.get("description") or {}).get("text", "") or ""
            companies.append(
                CompanyRaw(
                    name=name,
                    website=employer.get("url") or None,
                    city=address.get("city") or address.get("municipality") or city,
                    source="af",
                    job_title=hit.get("headline"),
                    job_url=hit.get("webpage_url"),
                    publication_date=hit.get("publication_date"),
                    description=desc or None,
                )
            )
        return companies, total
    except Exception as exc:
        logger.warning("AF parse failed: %s", exc)
        return [], 0
