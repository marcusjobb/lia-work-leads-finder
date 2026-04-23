import pytest
from unittest.mock import AsyncMock, patch

from cover_letter.models import StudentProfile
from cover_letter.pipeline.postprocess import postprocess

STUDENT = StudentProfile(
    name="Nisse Nilsson",
    education="YH Java-utvecklare",
    tech_stack=["Java"],
    experience="2 år support",
    languages=["svenska"],
    portfolio_url="https://github.com/nissenilsson",
    bio="Lösningsorienterad",
)


def _mock_llm(response: str):
    return patch("llm_client.complete", new=AsyncMock(return_value=response))


@pytest.mark.asyncio
async def test_removes_phone_number():
    cleaned = "Bra brev.\n\nNisse Nilsson"
    with _mock_llm(cleaned):
        result = await postprocess("Bra brev.\n\nNisse Nilsson\n073–456 78 90", STUDENT)
    assert "073" not in result


@pytest.mark.asyncio
async def test_removes_placeholder_email():
    cleaned = "Bra brev.\n\nNisse Nilsson"
    with _mock_llm(cleaned):
        result = await postprocess("Bra brev.\n\nNisse Nilsson\nnisse@email.se", STUDENT)
    assert "@" not in result


@pytest.mark.asyncio
async def test_keeps_portfolio_url():
    cleaned = "Se min portfolio: https://github.com/nissenilsson"
    with _mock_llm(cleaned):
        result = await postprocess(cleaned, STUDENT)
    assert "github.com/nissenilsson" in result


@pytest.mark.asyncio
async def test_removes_unrelated_url():
    cleaned = "Besök  för mer info."
    with _mock_llm(cleaned):
        result = await postprocess("Besök https://randomsite.com för mer info.", STUDENT)
    assert "randomsite.com" not in result


@pytest.mark.asyncio
async def test_preserves_letter_body():
    body = "Hej,\n\nJag söker LIA hos er.\n\nMed vänliga hälsningar,\nNisse Nilsson"
    with _mock_llm(body):
        result = await postprocess(body, STUDENT)
    assert "Jag söker LIA hos er." in result
    assert "Nisse Nilsson" in result


@pytest.mark.asyncio
async def test_strips_trailing_blank_lines():
    cleaned = "Bra brev."
    with _mock_llm(cleaned + "\n\n\n"):
        result = await postprocess("Bra brev.\n073–123 45 67\n\n\n", STUDENT)
    assert not result.endswith("\n")


@pytest.mark.asyncio
async def test_no_double_spaces_after_removal():
    cleaned = "Kontakt:  tack."
    with _mock_llm(cleaned):
        result = await postprocess("Kontakt: 073–123 45 67 och nisse@email.se tack.", STUDENT)
    assert "randomsite" not in result
