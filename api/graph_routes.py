"""
FastAPI router for Terra Graph API & Biometric Knowledge Engine.
"""

from fastapi import APIRouter
from data.mock_generator import generate_unified_profile
from models.graph_engine import TerraGraphEngine

router = APIRouter(prefix="/api/graph", tags=["Terra Graph API"])
graph_engine = TerraGraphEngine()


@router.get("/agp/{persona_id}")
async def get_agp_chart(persona_id: str):
    """
    Get Ambulatory Glucose Profile (AGP) compliant with Terra Graph API standard.
    Includes continuous 24h curve and Time-in-Range percentiles.
    """
    profile = generate_unified_profile(persona_id)
    return graph_engine.get_agp_graph_data(profile)


@router.get("/hypnogram/{persona_id}")
async def get_hypnogram(persona_id: str):
    """
    Get sleep architecture and hypnogram stage breakdown.
    """
    profile = generate_unified_profile(persona_id)
    return graph_engine.get_sleep_hypnogram(profile)


@router.get("/correlation/{persona_id}")
async def get_longitudinal_correlation(persona_id: str, days: int = 14):
    """
    Get multi-metric longitudinal series (HRV vs Sleep vs Workout Strain).
    """
    return graph_engine.get_longitudinal_correlation_series(persona_id, days=min(30, max(7, days)))


@router.get("/knowledge")
async def get_knowledge_graph():
    """
    Export the full health knowledge graph (Behaviors -> Biomarkers -> Health Goals).
    """
    return graph_engine.get_knowledge_graph_summary()


@router.get("/behavioral-impacts/{persona_id}")
async def get_behavioral_impacts(persona_id: str):
    """
    Trace causal downstream impacts of recent persona behaviors through the graph.
    """
    profile = generate_unified_profile(persona_id)
    return {
        "persona_id": persona_id,
        "logged_behaviors": profile.recent_behaviors,
        "causal_impacts": graph_engine.analyze_behavioral_impacts(profile)
    }


@router.get("/digital-twins/{persona_id}")
async def get_digital_twins(persona_id: str):
    """
    Find most similar biometric cohort matches (Digital Twins) via cosine similarity.
    """
    profile = generate_unified_profile(persona_id)
    twins = graph_engine.find_digital_twins(profile)
    return {
        "persona_id": persona_id,
        "digital_twins": twins
    }
