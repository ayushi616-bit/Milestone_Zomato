"""Integration tests for the Streamlit UI (src.app)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture(autouse=True)
def mock_store_data() -> MagicMock:
    """Mock store calls globally to prevent actual Hugging Face dataset loading."""
    with patch("src.data.store.get_locations") as mock_locs, \
         patch("src.data.store.get_cuisines") as mock_cuisines, \
         patch("src.data.store.get_restaurants") as mock_rests:
        mock_locs.return_value = ["basavanagudi", "basaveshwaranagar"]
        mock_cuisines.return_value = ["south indian", "north indian"]
        mock_rests.return_value = []
        yield (mock_locs, mock_cuisines, mock_rests)


@patch("src.orchestrator.recommend")
def test_streamlit_ui_elements(mock_recommend: MagicMock) -> None:
    """Test initial state of widgets, user interaction, and submit flows."""
    from src.orchestrator import RecommendationResponse
    from src.presentation.formatter import DisplayRecommendation

    # Setup mock response from orchestrator
    mock_recommend.return_value = RecommendationResponse(
        summary="Test overall summary.",
        recommendations=[
            DisplayRecommendation(
                name="Samskruti",
                cuisine="South Indian",
                rating="4.1★",
                cost="₹550 for two",
                explanation="Test explanation.",
                rank=1,
            )
        ],
        provider="groq",
        model="llama-3.1-8b-instant",
        latency_ms=100.0,
        relaxed=False,
        relaxed_filters=[],
    )

    # Initialize AppTest from app.py
    at = AppTest.from_file("src/app.py")
    at.run()

    # Verify initial page loads successfully and widgets exist
    assert not at.exception
    assert len(at.selectbox) >= 2  # Location, Budget
    assert len(at.multiselect) == 1  # Cuisines
    assert len(at.slider) == 1  # Rating
    assert len(at.text_area) == 1  # Additional preferences text area

    # Verify default widget values are populated correctly
    assert at.selectbox[0].value == "Basavanagudi"
    assert at.selectbox[1].value == "medium"
    assert at.multiselect[0].value == ["South Indian"]
    assert at.slider[0].value == 3.0

    # Simulate click on "Get Recommendations" button
    at.button[0].click().run()

    # Assert orchestrator is invoked with UI parameters
    mock_recommend.assert_called_once_with(
        location="basavanagudi",
        budget="medium",
        cuisine=["south indian"],
        min_rating=3.0,
        additional_preferences=None,
    )

