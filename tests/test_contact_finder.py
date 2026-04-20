import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pipeline.enrichment.contact_finder import find_contact


@pytest.mark.asyncio
async def test_finds_mailto():
    html = '<a href="mailto:jobs@example.com">Contact</a>'
    mock_resp = MagicMock(text=html, raise_for_status=MagicMock())
    with patch("pipeline.enrichment.contact_finder.httpx.AsyncClient") as mc:
        mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=AsyncMock(return_value=mock_resp)))
        mc.return_value.__aexit__ = AsyncMock(return_value=False)
        info, score = await find_contact("https://example.com")
    assert info.email == "jobs@example.com"
    assert score == 100.0


@pytest.mark.asyncio
async def test_finds_contact_page():
    html = '<a href="/kontakt">Kontakta oss</a>'
    mock_resp = MagicMock(text=html, raise_for_status=MagicMock())
    with patch("pipeline.enrichment.contact_finder.httpx.AsyncClient") as mc:
        mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=AsyncMock(return_value=mock_resp)))
        mc.return_value.__aexit__ = AsyncMock(return_value=False)
        info, score = await find_contact("https://example.com")
    assert info.contact_url is not None
    assert score == 60.0


@pytest.mark.asyncio
async def test_finds_careers_page():
    html = '<a href="/karriar">Karriär</a>'
    mock_resp = MagicMock(text=html, raise_for_status=MagicMock())
    with patch("pipeline.enrichment.contact_finder.httpx.AsyncClient") as mc:
        mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=AsyncMock(return_value=mock_resp)))
        mc.return_value.__aexit__ = AsyncMock(return_value=False)
        info, score = await find_contact("https://example.com")
    assert info.careers_page is not None
    assert score == 60.0


@pytest.mark.asyncio
async def test_no_contact_found():
    html = "<html><body><p>Welcome</p></body></html>"
    mock_resp = MagicMock(text=html, raise_for_status=MagicMock())
    with patch("pipeline.enrichment.contact_finder.httpx.AsyncClient") as mc:
        mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=AsyncMock(return_value=mock_resp)))
        mc.return_value.__aexit__ = AsyncMock(return_value=False)
        info, score = await find_contact("https://example.com")
    assert info.email is None
    assert score == 0.0


@pytest.mark.asyncio
async def test_none_website():
    info, score = await find_contact(None)
    assert score == 0.0


@pytest.mark.asyncio
async def test_network_error():
    with patch("pipeline.enrichment.contact_finder.httpx.AsyncClient") as mc:
        mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=AsyncMock(side_effect=Exception("timeout"))))
        mc.return_value.__aexit__ = AsyncMock(return_value=False)
        info, score = await find_contact("https://example.com")
    assert score == 0.0


@pytest.mark.asyncio
async def test_email_beats_contact_page():
    html = '<a href="mailto:hr@example.com">HR</a><a href="/kontakt">Kontakt</a>'
    mock_resp = MagicMock(text=html, raise_for_status=MagicMock())
    with patch("pipeline.enrichment.contact_finder.httpx.AsyncClient") as mc:
        mc.return_value.__aenter__ = AsyncMock(return_value=MagicMock(get=AsyncMock(return_value=mock_resp)))
        mc.return_value.__aexit__ = AsyncMock(return_value=False)
        info, score = await find_contact("https://example.com")
    assert score == 100.0
    assert info.email == "hr@example.com"
