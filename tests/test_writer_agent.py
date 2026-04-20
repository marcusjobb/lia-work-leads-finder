from unittest.mock import AsyncMock, patch

import pytest

from cover_letter.models import CompanyResearch, StudentProfile
from cover_letter.pipeline.writer_agent import generate_letter


def _make_student() -> StudentProfile:
    return StudentProfile(
        name="Anna Lindqvist",
        education="YH Java-utvecklare, 2024–2026",
        tech_stack=["Java", "Spring Boot"],
        experience="2 år supporttekniker",
        languages=["svenska"],
        bio="Nyfiken och lösningsorienterad",
    )


def _make_research() -> CompanyResearch:
    return CompanyResearch(
        company_name="Techbolaget AB",
        website="https://techbolaget.se",
        about_text="Vi bygger moderna system",
        values=["Öppenhet", "Kvalitet"],
        recent_news=["Ny Java-tjänst lanserad"],
        detected_language="svenska",
    )


@pytest.mark.asyncio
async def test_generate_letter_calls_llm():
    expected = "Hej! Jag vill söka LIA hos er..."

    with patch("cover_letter.pipeline.writer_agent.llm_client.complete", new=AsyncMock(return_value=expected)):
        result = await generate_letter(_make_student(), _make_research())

    assert result == expected


@pytest.mark.asyncio
async def test_generate_letter_prompt_contains_company_name():
    captured_prompt: list[str] = []

    async def capture(prompt: str) -> str:
        captured_prompt.append(prompt)
        return "brev"

    with patch("cover_letter.pipeline.writer_agent.llm_client.complete", new=capture):
        await generate_letter(_make_student(), _make_research())

    assert "Techbolaget AB" in captured_prompt[0]
    assert "Java" in captured_prompt[0]
