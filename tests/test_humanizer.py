import pytest
from unittest.mock import AsyncMock, patch

from cover_letter.pipeline.humanizer import humanize


@pytest.mark.asyncio
async def test_default_mode_prompt_mentions_lia():
    captured: list[str] = []

    async def capture(prompt: str) -> str:
        captured.append(prompt)
        return "brev"

    with patch("cover_letter.pipeline.humanizer.llm_client.complete", new=capture):
        await humanize("Hej, jag söker...")

    assert "LIA" in captured[0]


@pytest.mark.asyncio
async def test_senior_mode_prompt_does_not_mention_lia():
    captured: list[str] = []

    async def capture(prompt: str) -> str:
        captured.append(prompt)
        return "brev"

    with patch("cover_letter.pipeline.humanizer.llm_client.complete", new=capture):
        await humanize("Hej, jag söker...", search_mode="senior")

    assert "LIA" not in captured[0]


@pytest.mark.asyncio
async def test_junior_mode_prompt_does_not_mention_lia():
    captured: list[str] = []

    async def capture(prompt: str) -> str:
        captured.append(prompt)
        return "brev"

    with patch("cover_letter.pipeline.humanizer.llm_client.complete", new=capture):
        await humanize("Hej, jag söker...", search_mode="junior")

    assert "LIA" not in captured[0]
