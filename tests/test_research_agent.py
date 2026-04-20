from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import Response

from cover_letter.pipeline.research_agent import _detect_language, research_company
from models import CompanyRaw, ContactInfo, LeadProfile, ScoreBreakdown


def _make_lead(website: str | None = "https://example.com") -> LeadProfile:
    return LeadProfile(
        company_name="Techbolaget AB",
        website=website,
        city="Göteborg",
        tech_tags=["Java"],
        contact=ContactInfo(),
        score=75.0,
        score_breakdown=ScoreBreakdown(tech_match=80, geo=70, contact=60, activity=80, stability=70, seniority=50),
        match_reason="Matchar Java",
        tier="STRONG",
    )


@pytest.mark.asyncio
async def test_research_company_no_website():
    lead = _make_lead(website=None)
    result = await research_company(lead)
    assert result.about_text == ""
    assert result.detected_language == "svenska"


@pytest.mark.asyncio
async def test_research_company_parses_html():
    fixture = (Path(__file__).parent / "fixtures" / "company_about_sv.html").read_text()

    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 200
    mock_response.text = fixture

    lead = _make_lead()

    with patch("cover_letter.pipeline.research_agent.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        result = await research_company(lead)

    assert result.company_name == "Techbolaget AB"
    assert len(result.about_text) > 0
    assert result.detected_language == "svenska"


def test_detect_language_swedish():
    text = "Vi är ett bolag som jobbar med och för våra kunder"
    assert _detect_language(text) == "svenska"


def test_detect_language_english():
    text = "We are a company that works with and for our customers"
    assert _detect_language(text) == "engelska"
