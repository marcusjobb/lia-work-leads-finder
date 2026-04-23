import json
import re

import httpx
from bs4 import BeautifulSoup

import llm_client
from cover_letter.models import CompanyResearch
from models import LeadProfile

_ABOUT_PATHS = ["/about", "/om-oss", "/om", "/about-us", "/company"]
_JOBS_PATHS = ["/jobs", "/karriar", "/karriär", "/lediga-tjanster", "/lediga-tjänster"]

_SWEDISH_WORDS = re.compile(
    r"\b(och|att|det|är|för|med|som|på|en|ett|av|till|den|de|vi|inte|har|om|men|ska|kan|var)\b",
    re.IGNORECASE,
)
_ENGLISH_WORDS = re.compile(
    r"\b(the|and|is|for|with|that|on|an|of|to|we|not|have|about|but|will|can|was|our|you)\b",
    re.IGNORECASE,
)


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
    raw_text = soup.get_text(separator=" ", strip=True)
    detected_language = _detect_language(raw_text)

    extracted = await _extract_with_llm(lead.company_name, raw_text[:3000], detected_language)

    return CompanyResearch(
        company_name=lead.company_name,
        website=lead.website,
        about_text=extracted.get("about_text", raw_text[:2000]),
        values=extracted.get("values", []),
        recent_news=extracted.get("recent_news", []),
        detected_language=detected_language,
    )


async def _extract_with_llm(company_name: str, text: str, language: str) -> dict:
    prompt = (
        f'Du analyserar webbinnehåll för företaget "{company_name}" inför ett ansökningsbrev.\n'
        f'Svara BARA med JSON utan markdown:\n'
        f'{{\n'
        f'  "about_text": "2-3 meningar om vad företaget gör",\n'
        f'  "values": ["värdering1", "värdering2"],\n'
        f'  "recent_news": ["nyhet1", "nyhet2"]\n'
        f'}}\n'
        f'Max 5 values, max 3 recent_news. Tomma listor om inget hittas.\n'
        f'Språk i svaret: {language}\n\n'
        f'Webbinnehåll:\n{text}'
    )
    raw = await llm_client.complete(prompt)
    return _parse_json(raw)


def _detect_language(text: str) -> str:
    sv = len(_SWEDISH_WORDS.findall(text))
    en = len(_ENGLISH_WORDS.findall(text))
    return "svenska" if sv >= en else "engelska"


def _parse_json(text: str) -> dict:
    text = re.sub(r"```[a-z]*\n?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*?\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return {}


def _empty(company_name: str, website: str | None) -> CompanyResearch:
    return CompanyResearch(
        company_name=company_name,
        website=website,
        about_text="",
        values=[],
        recent_news=[],
        detected_language="svenska",
    )
