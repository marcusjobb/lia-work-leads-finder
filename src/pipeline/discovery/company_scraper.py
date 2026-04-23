import logging
import re

import httpx
from bs4 import BeautifulSoup

from models import CompanyRaw

logger = logging.getLogger(__name__)

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; LIA-Leads-Finder/1.0)"}
_ORG_RE = re.compile(r"/(\d{10})/")
_MAX_RESULTS = 10


async def scrape_companies(tech_stack: list[str], city: str) -> list[CompanyRaw]:
    """Search Allabolag.se for IT companies in city. Returns up to 10 CompanyRaw."""
    query = (tech_stack[0] if tech_stack else "IT").replace(" ", "+")
    city_q = city.replace(" ", "+")
    url = f"https://www.allabolag.se/vad/{query}/var/{city_q}"

    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True, headers=_HEADERS) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        logger.warning("Allabolag company scrape failed for %s/%s: %s", query, city, exc)
        return []

    companies: list[CompanyRaw] = []
    seen: set[str] = set()

    for tag in soup.find_all("a", href=_ORG_RE):
        href = tag["href"]
        name = tag.get_text(strip=True)
        if not name or name in seen:
            continue
        seen.add(name)
        full_url = ("https://www.allabolag.se" + href) if href.startswith("/") else href
        companies.append(
            CompanyRaw(
                name=name,
                website=full_url,
                city=city,
                source="allabolag",
            )
        )
        if len(companies) >= _MAX_RESULTS:
            break

    return companies
