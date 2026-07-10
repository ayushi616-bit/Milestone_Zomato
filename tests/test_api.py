"""Unit tests for the FastAPI backend (src.api)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from src.api import app


@pytest.fixture
def mock_api_store() -> MagicMock:
    """Mock store calls for API tests."""
    with patch("src.api.get_locations") as mock_locs, \
         patch("src.api.get_cuisines") as mock_cuisines:
        mock_locs.return_value = ["basavanagudi", "indiranagar"]
        mock_cuisines.return_value = ["south indian", "italian"]
        yield (mock_locs, mock_cuisines)


client = TestClient(app)


def test_root_endpoint() -> None:
    """Verify GET / returns healthy status."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_health_endpoint() -> None:
    """Verify GET /health returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_locations_endpoint(mock_api_store) -> None:
    """Verify GET /api/locations returns mocked locations."""
    response = client.get("/api/locations")
    assert response.status_code == 200
    assert response.json() == ["basavanagudi", "indiranagar"]


def test_cuisines_endpoint(mock_api_store) -> None:
    """Verify GET /api/cuisines returns mocked cuisines."""
    response = client.get("/api/cuisines")
    assert response.status_code == 200
    assert response.json() == ["south indian", "italian"]


@patch("src.api.recommend")
def test_recommend_endpoint(mock_recommend: MagicMock, mock_api_store) -> None:
    """Verify POST /api/recommend calls recommend orchestrator with correct params."""
    from src.orchestrator import RecommendationResponse
    from src.presentation.formatter import DisplayRecommendation

    mock_recommend.return_value = RecommendationResponse(
        summary="Tasty options found.",
        recommendations=[
            DisplayRecommendation(
                name="Toit",
                cuisine="Italian, Pizza",
                rating="4.4★",
                cost="₹1,500 for two",
                explanation="Great brewpub menu.",
                rank=1,
            )
        ],
        provider="groq",
        model="llama-3.1-8b-instant",
        latency_ms=80.0,
        relaxed=False,
        relaxed_filters=[],
    )

    payload = {
        "location": "Indiranagar",
        "budget": "medium",
        "cuisine": "Italian",
        "min_rating": 4.0,
        "additional_preferences": "great ambience",
        "results": 5,
    }

    response = client.post("/api/recommend", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    
    assert res_data["summary"] == "Tasty options found."
    assert len(res_data["recommendations"]) == 1
    assert res_data["recommendations"][0]["name"] == "Toit"
    assert res_data["recommendations"][0]["rank"] == 1

    mock_recommend.assert_called_once_with(
        location="indiranagar",
        budget="medium",
        cuisine=["italian"],
        min_rating=4.0,
        additional_preferences="great ambience",
        top_k=5,
    )
