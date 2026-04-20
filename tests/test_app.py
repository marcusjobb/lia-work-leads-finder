import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from models import CompanyRaw


@pytest.fixture
def client():
    from app import app
    return TestClient(app)


def test_index_page_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "stad" in response.text.lower() or "city" in response.text.lower()


def test_search_returns_results(client):
    fake_companies = [
        CompanyRaw(
            name="Sigma AB",
            city="Göteborg",
            source="indeed",
            job_title="Java Developer",
        )
    ]
    with patch("app.scrape_indeed", new=AsyncMock(return_value=fake_companies)), \
         patch("app.scrape_af", new=AsyncMock(return_value=([], 0))):
        response = client.post(
            "/search",
            data={"city": "Göteborg", "tech_stack": "Java"},
        )
    assert response.status_code == 200
    assert "Sigma AB" in response.text


def test_search_empty_results(client):
    with patch("app.scrape_indeed", new=AsyncMock(return_value=[])), \
         patch("app.scrape_af", new=AsyncMock(return_value=([], 0))):
        response = client.post(
            "/search",
            data={"city": "Göteborg", "tech_stack": "Java"},
        )
    assert response.status_code == 200
