import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from pipeline.discovery.indeed import scrape_indeed

FIXTURE = (Path(__file__).parent / "fixtures" / "indeed_results.html").read_text()


@pytest.mark.asyncio
async def test_scrape_returns_companies():
    mock_response = MagicMock()
    mock_response.text = FIXTURE
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.indeed.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(return_value=mock_response)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results = await scrape_indeed(["Java", "Spring Boot"], "Göteborg")

    assert len(results) == 2
    assert results[0].name == "Sigma AB"
    assert results[0].source == "indeed"
    assert results[0].city == "Göteborg"
    assert results[0].job_title == "Java Backend Developer"


@pytest.mark.asyncio
async def test_scrape_empty_on_error():
    with patch("pipeline.discovery.indeed.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(side_effect=Exception("network error"))
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results = await scrape_indeed(["Java"], "Göteborg")

    assert results == []
