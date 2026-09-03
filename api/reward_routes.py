"""
FastAPI router for Behavioral Rewards & User Retention Optimization.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from data.mock_generator import generate_unified_profile
from models.reward_optimizer import RewardOptimizer

router = APIRouter(prefix="/api/rewards", tags=["Rewards & Retention Engine"])
reward_optimizer = RewardOptimizer()


class StreakClaimRequest(BaseModel):
    persona_id: str = Field(..., json_schema_extra={"example": "alex_longevity"})
    current_streak_days: int = Field(14, ge=1)


@router.get("/{persona_id}")
async def get_daily_rewards(persona_id: str, streak_days: int = 12):
    """
    Get daily behavior rewards, streak multipliers, and retention churn risk analytics.
    """
    profile = generate_unified_profile(persona_id)
    return reward_optimizer.compute_daily_rewards(profile, current_streak_days=streak_days)


@router.post("/claim-streak")
async def claim_streak(request: StreakClaimRequest):
    """
    Claim daily habit streak and calculate milestone bonus points.
    """
    profile = generate_unified_profile(request.persona_id)
    result = reward_optimizer.compute_daily_rewards(
        profile,
        current_streak_days=request.current_streak_days + 1
    )
    result["streak_claimed"] = True
    result["new_streak_days"] = request.current_streak_days + 1
    return result
