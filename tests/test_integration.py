import pytest
from unittest.mock import AsyncMock, patch
from models import CompanyRaw, ContactInfo, SearchConfig
from pipeline.integration import build_profile


def test_build_profile_scores_tech():
    company = CompanyRaw(
        name="Sigma AB",
        city="Göteborg",
        source="indeed",
        job_title="Java Spring Boot Developer",
    )
    config = SearchConfig(city="Göteborg", tech_stack=["Java", "Spring Boot"])
    profile = build_profile(company, config)

    assert profile.company_name == "Sigma AB"
    assert profile.score_breakdown.tech_match >= 80
    assert profile.score_breakdown.geo == 100.0
    assert profile.tier in ("STRONG", "GOOD", "WEAK", "SKIP")
    assert "Java" in profile.match_reason or "Göteborg" in profile.match_reason


def test_build_profile_different_city():
    company = CompanyRaw(
        name="Acme AB", city="Stockholm", source="indeed", job_title="Java Developer"
    )
    config = SearchConfig(city="Göteborg", tech_stack=["Java"])
    profile = build_profile(company, config)

    assert profile.score_breakdown.geo == 30.0


@pytest.mark.asyncio
async def test_build_profile_async_finds_contact():
    from pipeline.integration import build_profile_async
    company = CompanyRaw(name="Sigma AB", city="Göteborg", source="af",
                         job_title="Python Developer", website="https://sigma.se")
    config = SearchConfig(city="Göteborg", tech_stack=["Python"])
    with patch("pipeline.integration.find_contact", new_callable=AsyncMock) as mock_fc:
        mock_fc.return_value = (ContactInfo(email="jobs@sigma.se"), 100.0)
        profile = await build_profile_async(company, config)
    assert profile.contact.email == "jobs@sigma.se"
    assert profile.score_breakdown.contact == 100.0
