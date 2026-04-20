import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pipeline.discovery.company_scraper import scrape_companies


def _mock_client(html: str):
    resp = MagicMock(text=html, raise_for_status=MagicMock())
    client = MagicMock()
    client.get = AsyncMock(return_value=resp)
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    return mock_cm


@pytest.mark.asyncio
async def test_extracts_companies():
    html = """
    <a href="/5566778899/sigma-ab">Sigma AB</a>
    <a href="/1122334455/nexer-ab">Nexer AB</a>
    """
    with patch("pipeline.discovery.company_scraper.httpx.AsyncClient", return_value=_mock_client(html)):
        results = await scrape_companies(["Python"], "Göteborg")
    assert len(results) == 2
    assert all(r.source == "allabolag" for r in results)
    assert results[0].name == "Sigma AB"
    assert results[1].name == "Nexer AB"


@pytest.mark.asyncio
async def test_empty_page_returns_empty():
    html = "<html><body><p>Inga resultat</p></body></html>"
    with patch("pipeline.discovery.company_scraper.httpx.AsyncClient", return_value=_mock_client(html)):
        results = await scrape_companies(["Python"], "Göteborg")
    assert results == []


@pytest.mark.asyncio
async def test_network_error_returns_empty():
    client = MagicMock()
    client.get = AsyncMock(side_effect=Exception("timeout"))
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    with patch("pipeline.discovery.company_scraper.httpx.AsyncClient", return_value=mock_cm):
        results = await scrape_companies(["Python"], "Göteborg")
    assert results == []


@pytest.mark.asyncio
async def test_limits_to_10_companies():
    links = "\n".join(
        f'<a href="/{str(i).zfill(10)}/company-{i}">Company {i}</a>'
        for i in range(15)
    )
    html = f"<html><body>{links}</body></html>"
    with patch("pipeline.discovery.company_scraper.httpx.AsyncClient", return_value=_mock_client(html)):
        results = await scrape_companies(["Python"], "Göteborg")
    assert len(results) == 10
