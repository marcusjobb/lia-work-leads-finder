import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from models import CompanyRaw, ContactInfo, LeadProfile, ScoreBreakdown


@pytest.fixture
def client():
    from app import app
    return TestClient(app)


def _make_profile(name="Sigma AB") -> LeadProfile:
    return LeadProfile(
        company_name=name,
        city="Göteborg",
        source="indeed",
        job_title="Java Developer",
        job_url="https://example.com/job/1",
        tech_tags=["java"],
        contact=ContactInfo(email="jobs@sigma.se"),
        score=70.0,
        score_breakdown=ScoreBreakdown(
            tech_match=100, geo=100, contact=100, activity=80, stability=50, seniority=50
        ),
        match_reason="Matchar Java, Göteborg",
        tier="STRONG",
    )


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "stad" in response.text.lower() or "city" in response.text.lower()


def test_search_returns_results(client):
    with patch("app.scrape_indeed", new=AsyncMock(return_value=[])), \
         patch("app.scrape_af", new=AsyncMock(return_value=([], 0))), \
         patch("app.scrape_companies", new=AsyncMock(return_value=[])), \
         patch("app.build_profile_async", new=AsyncMock(return_value=_make_profile())):
        # Trigger build_profile_async by providing one raw company
        with patch("app.scrape_indeed", new=AsyncMock(return_value=[
            CompanyRaw(name="Sigma AB", city="Göteborg", source="indeed", job_title="Java Developer")
        ])):
            response = client.post("/search", data={"city": "Göteborg", "tech_stack": "Java"})
    assert response.status_code == 200
    assert "Sigma AB" in response.text


def test_search_empty_results(client):
    with patch("app.scrape_indeed", new=AsyncMock(return_value=[])), \
         patch("app.scrape_af", new=AsyncMock(return_value=([], 0))), \
         patch("app.scrape_companies", new=AsyncMock(return_value=[])):
        response = client.post("/search", data={"city": "Göteborg", "tech_stack": "Java"})
    assert response.status_code == 200
