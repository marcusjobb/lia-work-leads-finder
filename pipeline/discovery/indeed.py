import logging
from urllib.parse import quote_plus

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from models import CompanyRaw

logger = logging.getLogger(__name__)


async def scrape_indeed(
    tech_stack: list[str], city: str, all_sweden: bool = False
) -> list[CompanyRaw]:
    """Scrape Indeed.se via Playwright → list[CompanyRaw]. Returns [] on error."""
    query = " ".join(tech_stack[:3])
    location = "" if all_sweden else city
    url = (
        f"https://se.indeed.com/jobs"
        f"?q={quote_plus(query)}&l={quote_plus(location)}&lang=sv"
    )

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.set_extra_http_headers({
                "Accept-Language": "sv-SE,sv;q=0.9,en;q=0.8",
            })
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(2000)
            html = await page.content()
            await browser.close()
    except Exception as exc:
        logger.warning("Indeed Playwright scrape failed: %s", exc)
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
