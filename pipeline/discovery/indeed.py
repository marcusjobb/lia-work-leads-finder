import logging
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from models import CompanyRaw

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
}


async def scrape_indeed(
    tech_stack: list[str], city: str, all_sweden: bool = False
) -> list[CompanyRaw]:
    """Scrape Indeed.se job listings → list[CompanyRaw]. Returns [] on error."""
    query = " ".join(tech_stack[:3])
    location = "" if all_sweden else city
    url = (
        f"https://se.indeed.com/jobs"
        f"?q={quote_plus(query)}&l={quote_plus(location)}&lang=sv"
    )

    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
            response = await client.get(url, headers=HEADERS)
            response.raise_for_status()
        html = response.text
    except Exception as exc:
        logger.warning("Indeed scrape failed: %s", exc)
        return []

    try:
        soup = BeautifulSoup(html, "html.parser")
        companies: list[CompanyRaw] = []

        for card in soup.select("div.job_seen_beacon"):
            name_el = card.select_one("span[data-testid='company-name']")
            if not name_el:
                continue

            location_el = card.select_one("div[data-testid='text-location']")
            title_el = card.select_one("h2.jobTitle a span")
            link_el = card.select_one("h2.jobTitle a")
            href = link_el.get("href") if link_el else None

            companies.append(
                CompanyRaw(
                    name=name_el.get_text(strip=True),
                    city=location_el.get_text(strip=True) if location_el else city,
                    source="indeed",
                    job_title=title_el.get_text(strip=True) if title_el else None,
                    job_url=f"https://se.indeed.com{href}" if href else None,
                )
            )

        return companies
    except Exception as exc:
        logger.warning("Indeed HTML parsing failed: %s", exc)
        return []
