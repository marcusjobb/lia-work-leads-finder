import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pipeline.discovery.af_scraper import scrape_af

MOCK_RESPONSE = {
    "hits": [
        {
            "headline": "Python Developer",
            "employer": {"name": "Acme AB"},
            "workplace_address": {"city": "Stockholm", "municipality": "Stockholm"},
            "webpage_url": "https://example.com/job/1",
        },
        {
            "headline": "Django Backend Engineer",
            "employer": {"name": "Tech AB"},
            "workplace_address": {"city": "Stockholm", "municipality": "Stockholm"},
            "webpage_url": "https://example.com/job/2",
        },
    ]
}


@pytest.mark.asyncio
async def test_scrape_returns_companies():
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_RESPONSE
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(return_value=mock_response)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python", "Django"], "Stockholm")

    assert len(results) == 2
    assert results[0].name == "Acme AB"
    assert results[0].source == "af"
    assert results[0].city == "Stockholm"
    assert results[0].job_title == "Python Developer"


@pytest.mark.asyncio
async def test_scrape_empty_on_error():
    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(side_effect=Exception("network error"))
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python"], "Stockholm")

    assert results == []


@pytest.mark.asyncio
async def test_skips_entries_without_employer_name():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hits": [{"headline": "Job", "employer": {}, "workplace_address": {}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(return_value=MagicMock(
            get=AsyncMock(return_value=mock_response)
        ))
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python"], "Stockholm")

    assert results == []


@pytest.mark.asyncio
async def test_extracts_publication_date():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hits": [
            {
                "headline": "Python Developer",
                "employer": {"name": "Acme AB"},
                "workplace_address": {"city": "Stockholm"},
                "webpage_url": "https://example.com/job/1",
                "publication_date": "2026-03-15T12:00:00",
            }
        ]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, _ = await scrape_af(["Python"], "Stockholm")

    assert results[0].publication_date == "2026-03-15T12:00:00"


@pytest.mark.asyncio
async def test_returns_total_hits():
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "total": {"value": 42},
        "hits": [
            {
                "headline": "Python Developer",
                "employer": {"name": "Acme AB"},
                "workplace_address": {"city": "Göteborg"},
                "webpage_url": "https://example.com/job/1",
                "publication_date": "2026-04-01T10:00:00",
            }
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(return_value=mock_response))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        results, total = await scrape_af(["Python"], "Göteborg")

    assert total == 42
    assert len(results) == 1


@pytest.mark.asyncio
async def test_always_fetches_from_offset_zero():
    mock_response = MagicMock()
    mock_response.json.return_value = {"total": {"value": 42}, "hits": []}
    mock_response.raise_for_status = MagicMock()

    captured_params = {}

    async def capture_get(url, **kwargs):
        captured_params.update(kwargs.get("params", {}))
        return mock_response

    with patch("pipeline.discovery.af_scraper.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=MagicMock(get=AsyncMock(side_effect=capture_get))
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
        await scrape_af(["Python"], "Göteborg")

    assert captured_params.get("offset") == 0
