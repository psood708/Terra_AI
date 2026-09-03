"""
FastAPI router for OdinAI Health Intelligence with Active LLM capabilities.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional
from data.mock_generator import generate_unified_profile
from models.odin_ai import OdinAIEngine

router = APIRouter(prefix="/api/odin", tags=["OdinAI Intelligence"])
odin_engine = OdinAIEngine()


class OdinQueryRequest(BaseModel):
    persona_id: str = Field(..., json_schema_extra={"example": "alex_longevity"})
    query: str = Field(..., json_schema_extra={"example": "Why is my recovery score at this level today and should I do heavy intervals?"})
    api_key: Optional[str] = Field(None, json_schema_extra={"example": "AIzaSy... or sk-..."}, description="Optional user Gemini or OpenAI API key")
    provider: Optional[str] = Field("gemini", json_schema_extra={"example": "gemini"}, description="LLM provider: gemini or openai")


class TestConnectionRequest(BaseModel):
    api_key: str = Field(..., json_schema_extra={"example": "AIzaSy..."})
    provider: Optional[str] = Field("gemini", json_schema_extra={"example": "gemini"})


@router.post("/query")
async def ask_odin(request: OdinQueryRequest):
    """
    Query OdinAI health companion.
    Uses active generative AI (Gemini / OpenAI) when an API key is provided,
    otherwise uses the built-in physiological reasoning engine.
    """
    profile = generate_unified_profile(request.persona_id)
    return await odin_engine.process_query(
        query_text=request.query,
        profile=profile,
        api_key=request.api_key,
        provider=request.provider or "gemini"
    )


@router.post("/test-connection")
async def test_llm_connection(request: TestConnectionRequest):
    """
    Test live API key connection against Google Gemini or OpenAI.
    Returns latency and exact model connectivity confirmation.
    """
    return await odin_engine.test_api_connection(
        api_key=request.api_key,
        provider=request.provider or "gemini"
    )


@router.get("/recovery/{persona_id}")
async def get_recovery_status(persona_id: str):
    """
    Get detailed recovery and autonomic nervous system readiness synthesis.
    """
    profile = generate_unified_profile(persona_id)
    return odin_engine.analyze_recovery_status(profile)


@router.get("/anomalies/{persona_id}")
async def get_active_anomalies(persona_id: str):
    """
    Detect biometric anomalies: acute HRV depression, nocturnal HR elevation, or glucose spikes.
    """
    profile = generate_unified_profile(persona_id)
    anomalies = odin_engine.detect_anomalies(profile)
    return {
        "persona_id": persona_id,
        "anomalies_count": len(anomalies),
        "anomalies": anomalies
    }


@router.get("/adaptive-workout/{persona_id}")
async def get_adaptive_workout(persona_id: str):
    """
    Get dynamic recovery-adjusted workout prescription based on current physiological strain.
    """
    profile = generate_unified_profile(persona_id)
    return odin_engine.generate_adaptive_workout_plan(profile)
