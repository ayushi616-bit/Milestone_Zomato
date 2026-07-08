"""Unit and integration tests for the orchestrator (src.orchestrator)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from src.data.models import Restaurant
from src.orchestrator import recommend, RecommendationResponse
from src.validators import ValidationError
from src.llm.client import LLMError


@pytest.fixture
def mock_llm_response() -> str:
    return """
    {
      "summary": "AI recommendation summary.",
      "recommendations": [
        {
          "restaurant_id": "r_1042",
          "rank": 1,
          "explanation": "Excellent mock Italian recommendation."
        }
      ]
    }
    """


@pytest.fixture
def mock_restaurants(sample_restaurant: Restaurant) -> list[Restaurant]:
    return [sample_restaurant]


@patch("src.orchestrator.get_restaurants")
@patch("src.orchestrator.get_llm_client")
def test_recommend_happy_path(
    mock_get_llm_client: MagicMock,
    mock_get_restaurants: MagicMock,
    mock_restaurants: list[Restaurant],
    mock_llm_response: str,
) -> None:
    # Setup mocks
    mock_get_restaurants.return_value = mock_restaurants

    mock_client = MagicMock()
    mock_client.generate.return_value = mock_llm_response
    mock_get_llm_client.return_value = mock_client

    response = recommend(
        location="bangalore",
        budget="medium",
        cuisine="italian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )

    assert isinstance(response, RecommendationResponse)
    assert response.summary == "AI recommendation summary."
    assert len(response.recommendations) == 1
    rec = response.recommendations[0]
    assert rec.name == "Example Bistro"
    assert rec.cuisine == "Italian, Continental"
    assert rec.rating == "4.2★"
    assert rec.cost == "₹800 for two"
    assert rec.explanation == "Excellent mock Italian recommendation."
    assert rec.rank == 1
    assert response.relaxed is False
    assert response.relaxed_filters == []

    # Assert generate was called once
    mock_client.generate.assert_called_once()


@patch("src.orchestrator.get_restaurants")
@patch("src.orchestrator.get_llm_client")
def test_recommend_empty_candidates_no_llm_call(
    mock_get_llm_client: MagicMock,
    mock_get_restaurants: MagicMock,
) -> None:
    # Return empty restaurants
    mock_get_restaurants.return_value = []
    mock_client = MagicMock()
    mock_get_llm_client.return_value = mock_client

    response = recommend(
        location="bangalore",
        budget="medium",
        cuisine="italian",
        min_rating=4.0,
    )

    assert len(response.recommendations) == 0
    assert "No restaurants matching" in response.summary
    assert response.relaxed is True

    # Assert generate was NOT called
    mock_client.generate.assert_not_called()


@patch("src.orchestrator.get_restaurants")
@patch("src.orchestrator.get_llm_client")
def test_recommend_llm_parse_failure_retry_success(
    mock_get_llm_client: MagicMock,
    mock_get_restaurants: MagicMock,
    mock_restaurants: list[Restaurant],
    mock_llm_response: str,
) -> None:
    mock_get_restaurants.return_value = mock_restaurants
    mock_client = MagicMock()
    # First call returns malformed JSON, second call returns valid JSON
    mock_client.generate.side_effect = ["malformed-json", mock_llm_response]
    mock_get_llm_client.return_value = mock_client

    response = recommend(
        location="bangalore",
        budget="medium",
        cuisine="italian",
        min_rating=4.0,
    )

    assert len(response.recommendations) == 1
    assert response.summary == "AI recommendation summary."
    assert mock_client.generate.call_count == 2


@patch("src.orchestrator.get_restaurants")
@patch("src.orchestrator.get_llm_client")
def test_recommend_llm_failure_fallback_rating_sort(
    mock_get_llm_client: MagicMock,
    mock_get_restaurants: MagicMock,
    mock_restaurants: list[Restaurant],
) -> None:
    mock_get_restaurants.return_value = mock_restaurants
    mock_client = MagicMock()
    # Always fails
    mock_client.generate.side_effect = LLMError("API failure")
    mock_get_llm_client.return_value = mock_client

    response = recommend(
        location="bangalore",
        budget="medium",
        cuisine="italian",
        min_rating=4.0,
    )

    assert len(response.recommendations) == 1
    assert "AI explanations unavailable" in response.summary
    assert response.recommendations[0].name == "Example Bistro"


def test_recommend_validation_error() -> None:
    with pytest.raises(ValidationError):
        recommend(
            location="",
            budget="invalid-budget",
            cuisine="italian",
            min_rating=6.0,
        )
