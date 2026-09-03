"""
FastAPI router for Biological Age, Trajectory Forecasting & Counterfactuals.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from data.mock_generator import generate_unified_profile
from models.health_predictor import HealthPredictor
from config import PERSONAS

router = APIRouter(prefix="/api/health-score", tags=["Health Forecasting & Longevity"])
health_predictor = HealthPredictor()


class WhatIfRequest(BaseModel):
    persona_id: str = Field(..., json_schema_extra={"example": "alex_longevity"})
    added_sleep_minutes: int = Field(30, ge=0, le=180)
    added_zone2_minutes_weekly: int = Field(60, ge=0, le=300)
    earlier_dinner_shift_hours: float = Field(2.0, ge=0.0, le=5.0)
    improved_glucose_tir_pct: float = Field(8.0, ge=0.0, le=30.0)


@router.get("/personas")
async def list_personas():
    """
    List all supported personas with their targets, objectives, and baseline sensors.
    """
    return list(PERSONAS.values())


@router.get("/bio-age/{persona_id}")
async def get_bio_age(persona_id: str):
    """
    Compute phenotypic biological age vs chronological age from multi-sensor biomarkers.
    """
    profile = generate_unified_profile(persona_id)
    return health_predictor.compute_biological_age(profile)


@router.get("/trajectory/{persona_id}")
async def get_health_trajectory(persona_id: str):
    """
    Get 10-year trajectory forecast comparing Status Quo vs Terra AI Guided longevity.
    """
    profile = generate_unified_profile(persona_id)
    return health_predictor.forecast_trajectory(profile)


@router.post("/what-if")
async def simulate_what_if(request: WhatIfRequest):
    """
    Simulate counterfactual lifestyle shifts and calculate projected biological age deceleration.
    """
    profile = generate_unified_profile(request.persona_id)
    return health_predictor.simulate_what_if_counterfactual(
        profile=profile,
        added_sleep_minutes=request.added_sleep_minutes,
        added_zone2_minutes_weekly=request.added_zone2_minutes_weekly,
        earlier_dinner_shift_hours=request.earlier_dinner_shift_hours,
        improved_glucose_tir_pct=request.improved_glucose_tir_pct
    )
