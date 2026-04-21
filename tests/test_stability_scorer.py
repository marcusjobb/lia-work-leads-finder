import pytest
from datetime import date
from unittest.mock import AsyncMock, patch

from pipeline.enrichment.stability_scorer import _age_score, score_stability
from pipeline.enrichment.company_api import CompanyApiData

TODAY = date.today().year


def test_age_score_10_plus():
    assert _age_score(f"{TODAY - 15}-03-01") == 100.0


def test_age_score_5_to_9():
    assert _age_score(f"{TODAY - 7}-01-01") == 75.0


def test_age_score_2_to_4():
    assert _age_score(f"{TODAY - 3}-06-01") == 50.0


def test_age_score_under_2():
    assert _age_score(f"{TODAY - 1}-01-01") == 20.0


def test_age_score_invalid():
    assert _age_score(None) == 50.0
    assert _age_score("bad-date") == 50.0


@pytest.mark.asyncio
async def test_uses_composite_score_when_available():
    mock_data = CompanyApiData(composite_score=82.0, is_active=True)
    with patch("pipeline.enrichment.stability_scorer.fetch_company", AsyncMock(return_value=mock_data)):
        score = await score_stability("Sigma AB", "Göteborg")
    assert score == 82.0


@pytest.mark.asyncio
async def test_falls_back_to_age_score():
    mock_data = CompanyApiData(registration_date=f"{TODAY - 12}-01-01", is_active=True)
    with patch("pipeline.enrichment.stability_scorer.fetch_company", AsyncMock(return_value=mock_data)):
        score = await score_stability("Test AB", "Stockholm")
    assert score == 100.0


@pytest.mark.asyncio
async def test_inactive_company_returns_low_score():
    mock_data = CompanyApiData(is_active=False, registration_date=f"{TODAY - 10}-01-01")
    with patch("pipeline.enrichment.stability_scorer.fetch_company", AsyncMock(return_value=mock_data)):
        score = await score_stability("Stängt AB", "Stockholm")
    assert score == 10.0


@pytest.mark.asyncio
async def test_api_failure_returns_neutral():
    with patch("pipeline.enrichment.stability_scorer.fetch_company", AsyncMock(side_effect=Exception("timeout"))):
        score = await score_stability("Okänt AB", "Göteborg")
    assert score == 50.0


@pytest.mark.asyncio
async def test_no_data_returns_neutral():
    mock_data = CompanyApiData()
    with patch("pipeline.enrichment.stability_scorer.fetch_company", AsyncMock(return_value=mock_data)):
        score = await score_stability("Okänt AB", "Göteborg")
    assert score == 50.0
