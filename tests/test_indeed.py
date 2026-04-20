import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from pipeline.discovery.indeed import scrape_indeed

FIXTURE = (Path(__file__).parent / "fixtures" / "indeed_results.html").read_text()


@pytest.mark.asyncio
async def test_scrape_returns_companies():
    mock_page = AsyncMock()
    mock_page.content = AsyncMock(return_value=FIXTURE)
    mock_page.goto = AsyncMock()
    mock_page.set_extra_http_headers = AsyncMock()
    mock_page.wait_for_timeout = AsyncMock()

    mock_browser = AsyncMock()
    mock_browser.new_page = AsyncMock(return_value=mock_page)
    mock_browser.close = AsyncMock()

    mock_chromium = AsyncMock()
    mock_chromium.launch = AsyncMock(return_value=mock_browser)

    mock_playwright = AsyncMock()
    mock_playwright.chromium = mock_chromium
    mock_playwright.__aenter__ = AsyncMock(return_value=mock_playwright)
    mock_playwright.__aexit__ = AsyncMock(return_value=False)

    with patch("pipeline.discovery.indeed.async_playwright", return_value=mock_playwright):
        results = await scrape_indeed(["Java", "Spring Boot"], "Göteborg")

    assert len(results) == 2
    assert results[0].name == "Sigma AB"
    assert results[0].source == "indeed"
    assert results[0].city == "Göteborg"
    assert results[0].job_title == "Java Backend Developer"


@pytest.mark.asyncio
async def test_scrape_empty_on_error():
    mock_playwright = AsyncMock()
    mock_playwright.__aenter__ = AsyncMock(side_effect=Exception("playwright error"))
    mock_playwright.__aexit__ = AsyncMock(return_value=False)

    with patch("pipeline.discovery.indeed.async_playwright", return_value=mock_playwright):
        results = await scrape_indeed(["Java"], "Göteborg")

    assert results == []
