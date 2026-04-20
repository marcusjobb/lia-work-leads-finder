import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_complete_routes_to_openrouter(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    import llm_client
    with patch.object(llm_client, "_openrouter", new=AsyncMock(return_value="svar")) as mock:
        result = await llm_client.complete("hej")
    mock.assert_called_once_with("hej")
    assert result == "svar"


@pytest.mark.asyncio
async def test_complete_routes_to_claude_cli(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "claude-cli")

    import llm_client
    with patch.object(llm_client, "_claude_cli", new=AsyncMock(return_value="svar")) as mock:
        result = await llm_client.complete("hej")
    mock.assert_called_once_with("hej")
    assert result == "svar"


@pytest.mark.asyncio
async def test_unknown_provider_raises(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "unknown")

    import llm_client
    with pytest.raises(ValueError, match="Unknown LLM_PROVIDER"):
        await llm_client.complete("hej")
