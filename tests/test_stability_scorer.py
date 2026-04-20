import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

from pipeline.enrichment.stability_scorer import (
    _age_score,
    _employee_score,
    score_stability,
)

TODAY = date.today().year


def test_age_score_10_plus():
    assert _age_score(TODAY - 15) == 100.0


def test_age_score_5_to_9():
    assert _age_score(TODAY - 7) == 75.0


def test_age_score_2_to_4():
    assert _age_score(TODAY - 3) == 50.0


def test_age_score_under_2():
    assert _age_score(TODAY - 1) == 20.0


def test_employee_score_large():
    assert _employee_score(200) == 100.0


def test_employee_score_medium():
    assert _employee_score(50) == 85.0


def test_employee_score_small():
    assert _employee_score(10) == 60.0


def test_employee_score_micro():
    assert _employee_score(3) == 30.0


def test_employee_score_solo():
    assert _employee_score(1) == 10.0


def _mock_client(responses: list):
    def make_resp(html):
        r = MagicMock()
        r.text = html
        r.raise_for_status = MagicMock()
        return r

    client = MagicMock()
    client.get = AsyncMock(side_effect=[make_resp(h) for h in responses])
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return mock_cm


@pytest.mark.asyncio
async def test_finds_company_age_and_employees():
    search_html = '<a href="/5566778899/sigma-ab">Sigma AB</a>'
    company_html = f'<p>Registrerad: {TODAY - 15}</p><p>45 anställda</p>'

    with patch("pipeline.enrichment.stability_scorer.httpx.AsyncClient", return_value=_mock_client([search_html, company_html])):
        score = await score_stability("Sigma AB", "Göteborg")

    assert score == 92.5  # (100.0 + 85.0) / 2


@pytest.mark.asyncio
async def test_only_age_available():
    search_html = '<a href="/1234567890/test-ab">Test AB</a>'
    company_html = f'<p>Registrerad: {TODAY - 12}</p>'

    with patch("pipeline.enrichment.stability_scorer.httpx.AsyncClient", return_value=_mock_client([search_html, company_html])):
        score = await score_stability("Test AB", "Stockholm")

    assert score == 100.0


@pytest.mark.asyncio
async def test_no_company_link_returns_neutral():
    search_html = "<html><body>Inga resultat</body></html>"

    with patch("pipeline.enrichment.stability_scorer.httpx.AsyncClient", return_value=_mock_client([search_html])):
        score = await score_stability("Okänt AB", "Göteborg")

    assert score == 50.0


@pytest.mark.asyncio
async def test_network_error_returns_neutral():
    client = MagicMock()
    client.get = AsyncMock(side_effect=Exception("timeout"))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)

    with patch("pipeline.enrichment.stability_scorer.httpx.AsyncClient", return_value=mock_cm):
        score = await score_stability("Sigma AB", "Göteborg")

    assert score == 50.0
