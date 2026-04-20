import re

import httpx
from bs4 import BeautifulSoup

from cover_letter.models import CompanyResearch
from models import LeadProfile

_SWEDISH_WORDS = re.compile(
    r"\b(och|att|det|är|för|med|som|på|en|ett|av|till|den|de|vi|inte|har|om|men|ska|kan|var)\b",
    re.IGNORECASE,
)
_ENGLISH_WORDS = re.compile(
    r"\b(the|and|is|for|with|that|on|an|of|to|we|not|have|about|but|will|can|was|our|you)\b",
    re.IGNORECASE,
)

_ABOUT_PATHS = ["/about", "/om-oss", "/om", "/about-us", "/company"]
_JOBS_PATHS = ["/jobs", "/karriar", "/karriär", "/lediga-tjanster", "/lediga-tjänster"]


async def research_company(lead: LeadProfile) -> CompanyResearch:
    if not lead.website:
        return _empty(lead.company_name, lead.website)

    base = lead.website.rstrip("/")
    collected: list[str] = []

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for path in [""] + _ABOUT_PATHS + _JOBS_PATHS:
            try:
                resp = await client.get(f"{base}{path}")
                if resp.status_code == 200:
                    collected.append(resp.text)
                    if len(collected) >= 3:
                        break
            except httpx.HTTPError:
                continue

    combined = " ".join(collected)
    soup = BeautifulSoup(combined, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    return CompanyResearch(
        company_name=lead.company_name,
        website=lead.website,
        about_text=text[:2000],
        values=_extract_values(soup),
        recent_news=_extract_news(soup),
        detected_language=_detect_language(text),
    )


def _detect_language(text: str) -> str:
    sv = len(_SWEDISH_WORDS.findall(text))
    en = len(_ENGLISH_WORDS.findall(text))
    return "svenska" if sv >= en else "engelska"


def _extract_values(soup: BeautifulSoup) -> list[str]:
    values: list[str] = []
    for tag in soup.find_all(["li", "p"]):
        t = tag.get_text(strip=True)
        if 10 < len(t) < 120 and any(
            kw in t.lower()
            for kw in ["värde", "value", "mission", "vision", "kultur", "culture"]
        ):
            values.append(t)
    return values[:5]


def _extract_news(soup: BeautifulSoup) -> list[str]:
    news: list[str] = []
    for tag in soup.find_all(["h2", "h3", "article"]):
        t = tag.get_text(strip=True)
        if 20 < len(t) < 200:
            news.append(t)
    return news[:3]


def _empty(company_name: str, website: str | None) -> CompanyResearch:
    return CompanyResearch(
        company_name=company_name,
        website=website,
        about_text="",
        values=[],
        recent_news=[],
        detected_language="svenska",
    )
