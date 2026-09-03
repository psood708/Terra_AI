"""
Pydantic Schemas representing Terra's Unified Data Models.
Matches Terra's standardized payload contracts across 500+ wearable sources.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class HeartRateZones(BaseModel):
    zone1_minutes: float = Field(..., description="Active Recovery (<60% max HR)")
    zone2_minutes: float = Field(..., description="Endurance Base / Mitochondrial (60-70% max HR)")
    zone3_minutes: float = Field(..., description="Aerobic Tempo (70-80% max HR)")
    zone4_minutes: float = Field(..., description="Lactate Threshold (80-90% max HR)")
    zone5_minutes: float = Field(..., description="Neuromuscular / VO2 Peak (>90% max HR)")


class TerraDailyPayload(BaseModel):
    timestamp: str
    steps: int = Field(..., ge=0)
    active_calories: float = Field(..., ge=0)
    resting_calories: float = Field(..., ge=0)
    distance_meters: float = Field(..., ge=0)
    resting_heart_rate_bpm: float = Field(..., ge=30, le=220)
    avg_heart_rate_bpm: float = Field(..., ge=30, le=220)
    max_heart_rate_bpm: float = Field(..., ge=30, le=240)
    floors_climbed: Optional[int] = 0
    estimated_vo2_max: Optional[float] = None


class SleepStageDurations(BaseModel):
    deep_sleep_seconds: int = Field(..., ge=0)
    rem_sleep_seconds: int = Field(..., ge=0)
    light_sleep_seconds: int = Field(..., ge=0)
    awake_seconds: int = Field(..., ge=0)


class TerraSleepPayload(BaseModel):
    start_time: str
    end_time: str
    duration_total_seconds: int = Field(..., ge=0)
    duration_asleep_seconds: int = Field(..., ge=0)
    sleep_efficiency_pct: float = Field(..., ge=0.0, le=100.0)
    sleep_score: int = Field(..., ge=0, le=100)
    stages: SleepStageDurations
    avg_hrv_rmssd_ms: float = Field(..., ge=5.0, le=300.0)
    lowest_heart_rate_bpm: float = Field(..., ge=30.0, le=150.0)
    respiratory_rate_rpm: float = Field(..., ge=8.0, le=30.0)
    temperature_deviation_c: Optional[float] = 0.0


class TerraActivityPayload(BaseModel):
    activity_id: str
    activity_name: str
    start_time: str
    duration_seconds: int = Field(..., ge=0)
    calories_burned: float = Field(..., ge=0)
    avg_hr_bpm: float = Field(..., ge=40, le=220)
    max_hr_bpm: float = Field(..., ge=50, le=240)
    hr_zones: HeartRateZones
    strain_score: float = Field(..., ge=0.0, le=21.0, description="Whoop/Terra strain scale (0-21)")


class GlucoseSample(BaseModel):
    timestamp: str
    glucose_mg_dl: float = Field(..., ge=20.0, le=500.0)


class TerraBodyPayload(BaseModel):
    timestamp: str
    weight_kg: float = Field(..., ge=30.0, le=300.0)
    bmi: float = Field(..., ge=12.0, le=60.0)
    body_fat_pct: Optional[float] = Field(None, ge=3.0, le=60.0)
    blood_pressure_systolic: Optional[int] = Field(None, ge=70, le=250)
    blood_pressure_diastolic: Optional[int] = Field(None, ge=40, le=150)
    fasting_glucose_mg_dl: Optional[float] = None
    cgm_readings_24h: Optional[List[GlucoseSample]] = []


class UnifiedHealthProfile(BaseModel):
    user_id: str
    persona_id: str
    date: str
    daily: TerraDailyPayload
    sleep: TerraSleepPayload
    activities: List[TerraActivityPayload]
    body: TerraBodyPayload
    recent_behaviors: List[Dict[str, Any]] = []


class TerraWebhookEvent(BaseModel):
    event_id: str
    event_type: str = Field(..., description="e.g. daily, sleep, activity, body")
    user_id: str
    timestamp: str
    data: Dict[str, Any]
