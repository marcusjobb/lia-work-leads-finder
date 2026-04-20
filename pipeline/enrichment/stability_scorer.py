import logging
import re
from datetime import date

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept-Language": "sv-SE,sv;q=0.9",
}
_ORG_HREF_RE = re.compile(r"/\d{10}/")
_YEAR_RE = re.compile(r"\b((?:19|20)\d{2})\b")
_EMP_RE = re.compile(r"(\d+)\s*(?:–|-|till\s*\d+\s*)?(?:anställda|medarbetare|employees)", re.I)
_TODAY_YEAR = date.today().year


def _age_score(founded_year: int) -> float:
    age = _TODAY_YEAR - founded_year
    if age >= 10:
        return 100.0
    if age >= 5:
        return 75.0
    if age >= 2:
        return 50.0
    return 20.0


def _employee_score(count: int) -> float:
    if count >= 100:
        return 100.0
    if count >= 20:
        return 85.0
    if count >= 5:
        return 60.0
    if count >= 2:
        return 30.0
    return 10.0


def _extract_year(soup: BeautifulSoup) -> int | None:
    for tag in soup.find_all(string=_YEAR_RE):
        parent = tag.parent
        if parent is None:
            continue
        context = (parent.get_text(" ", strip=True) + " " + (parent.get("class") or [""])[0]).lower()
        if any(k in context for k in ("registrerad", "bildad", "grundad", "start", "datum")):
            m = _YEAR_RE.search(tag)
            if m:
                yr = int(m.group(1))
                if 1850 <= yr <= _TODAY_YEAR:
                    return yr
    return None


def _extract_employees(soup: BeautifulSoup) -> int | None:
    m = _EMP_RE.search(soup.get_text(" ", strip=True))
    return int(m.group(1)) if m else None


async def score_stability(company_name: str, city: str) -> float:
    """Scrape Allabolag.se for company age + employee count. Returns 0–100, 50 on failure."""
    query = company_name.replace(" ", "+")
    city_q = city.replace(" ", "+")
    search_url = f"https://www.allabolag.se/vad/{query}/var/{city_q}"

    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers=_HEADERS) as client:
            resp = await client.get(search_url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")

            link = soup.find("a", href=_ORG_HREF_RE)
            if not link:
                return 50.0

            href = link["href"]
            company_url = ("https://www.allabolag.se" + href) if href.startswith("/") else href
            resp2 = await client.get(company_url)
            resp2.raise_for_status()
            soup2 = BeautifulSoup(resp2.text, "html.parser")
    except Exception as exc:
        logger.warning("Allabolag failed for %s: %s", company_name, exc)
        return 50.0

    scores = []
    yr = _extract_year(soup2)
    if yr:
        scores.append(_age_score(yr))
    emp = _extract_employees(soup2)
    if emp is not None:
        scores.append(_employee_score(emp))

    return round(sum(scores) / len(scores), 2) if scores else 50.0
