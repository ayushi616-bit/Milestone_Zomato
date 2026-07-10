"""FastAPI Web Server for Zomato AI Restaurant Recommendations.

Provides REST endpoints to query locations, cuisines, and generate AI-ranked
recommendations, preloading the dataset at startup to minimize latency.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.data.store import get_restaurants, get_locations, get_cuisines
from src.orchestrator import recommend, RecommendationResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle context manager to load and cache the dataset on startup."""
    logger.info("Initializing dataset cache at startup...")
    try:
        # Force load/cache of the Hugging Face dataset
        get_restaurants()
        logger.info("Dataset cache preloaded successfully.")
    except Exception as e:
        logger.exception("Failed to preload dataset cache during startup:")
    yield


app = FastAPI(
    title="TasteFinder AI API",
    description="API backend for Zomato-inspired AI restaurant recommendation system.",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS to allow access from the React frontend.
# If ALLOWED_ORIGINS is unset or empty, it defaults to "*" (e.g. for deployment / preview).
raw_origins = os.getenv("ALLOWED_ORIGINS", "*").strip()
if not raw_origins:
    raw_origins = "*"

allowed_origins = [
    origin.strip() 
    for origin in raw_origins.split(",") 
    if origin.strip()
]

# If allowed_origins contains "*", allow_credentials must be False to avoid browser CORS errors
allow_credentials = True
if "*" in allowed_origins:
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Health check endpoint returning a simple status message."""
    return {"status": "healthy", "service": "TasteFinder AI API"}


@app.get("/health")
def read_health():
    """Detailed health check endpoint."""
    return {"status": "healthy", "service": "TasteFinder AI API"}

class RecommendationRequest(BaseModel):
    """Pydantic model representing the client request query parameters."""
    location: str = Field(..., description="Target location/neighborhood in Bangalore")
    budget: str = Field("medium", description="Budget tier: 'low', 'medium', or 'high'")
    cuisine: str = Field(..., description="Comma-separated or single cuisine string")
    min_rating: float = Field(3.0, description="Minimum rating (0.0 to 5.0)")
    additional_preferences: Optional[str] = Field(None, description="Free-text instructions for LLM ranking")
    results: int = Field(5, description="Number of results to return (1 to 20)")


@app.get("/api/locations", response_model=List[str])
def read_locations():
    """Retrieve the sorted list of unique Bangalore locations available in the dataset."""
    try:
        return get_locations()
    except Exception as e:
        logger.exception("Error fetching locations:")
        raise HTTPException(status_code=500, detail=f"Failed to fetch locations: {e}")


@app.get("/api/cuisines", response_model=List[str])
def read_cuisines():
    """Retrieve the sorted list of unique cuisines available in the dataset."""
    try:
        return get_cuisines()
    except Exception as e:
        logger.exception("Error fetching cuisines:")
        raise HTTPException(status_code=500, detail=f"Failed to fetch cuisines: {e}")


@app.post("/api/recommend")
def post_recommend(req: RecommendationRequest):
    """Coordinate constraints filtering and LLM re-ranking to get personalized recommendations."""
    try:
        cuisine_list = [c.strip().lower() for c in req.cuisine.split(",") if c.strip()]
        
        # Call the orchestrator recommend pipeline
        response = recommend(
            location=req.location.lower().strip(),
            budget=req.budget.lower().strip(),
            cuisine=cuisine_list,
            min_rating=req.min_rating,
            additional_preferences=req.additional_preferences or None,
            top_k=req.results,
        )
        
        return {
            "summary": response.summary,
            "recommendations": [
                {
                    "rank": r.rank,
                    "name": r.name,
                    "location": r.location,
                    "rating": r.rating,
                    "cost": r.cost,
                    "cuisine": r.cuisine,
                    "explanation": r.explanation,
                }
                for r in response.recommendations
            ],
            "provider": response.provider,
            "model": response.model,
            "latency_ms": response.latency_ms,
            "relaxed": response.relaxed,
            "relaxed_filters": response.relaxed_filters,
        }
    except Exception as e:
        logger.exception("Error generating recommendations:")
        raise HTTPException(status_code=500, detail=str(e))
