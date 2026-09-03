"""
Realistic Synthetic Health Telemetry Generator matching Terra's Data Specs.
Generates multimodal wearable streams: CGM glucose, sleep hypnograms, HRV, activities.
"""

import math
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any

from data.terra_schemas import (
    TerraDailyPayload,
    TerraSleepPayload,
    SleepStageDurations,
    TerraActivityPayload,
    HeartRateZones,
    TerraBodyPayload,
    GlucoseSample,
    UnifiedHealthProfile
)
from config import PERSONAS


def generate_cgm_series(persona_id: str, date_str: str) -> List[GlucoseSample]:
    """
    Generate 24-hour continuous glucose monitor (CGM) curve (every 10 minutes = 144 samples).
    Demonstrates Ambulatory Glucose Profile (AGP) dynamics.
    """
    samples = []
    base_date = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Baseline parameters per persona
    if persona_id == "alex_longevity":
        fasting_base = 84.0
        meal_spike_factor = 28.0
        decay_rate = 0.85
    elif persona_id == "sarah_athlete":
        fasting_base = 88.0
        meal_spike_factor = 32.0
        decay_rate = 0.90
    elif persona_id == "marcus_metabolic":
        fasting_base = 118.0
        meal_spike_factor = 65.0
        decay_rate = 0.72  # Slower clearance (insulin resistance)
    else:  # elena_cognitive
        fasting_base = 90.0
        meal_spike_factor = 34.0
        decay_rate = 0.82

    current_glucose = fasting_base

    for i in range(144):
        sample_time = base_date + timedelta(minutes=i * 10)
        hour = sample_time.hour + sample_time.minute / 60.0
        
        # Dawn phenomenon (5 AM - 7 AM slight rise)
        dawn_effect = 6.0 * math.exp(-((hour - 6.5) ** 2) / 1.5) if 5 <= hour <= 8 else 0.0
        
        # Meal spikes (Breakfast ~8:00, Lunch ~13:00, Dinner ~19:30)
        meal_effect = 0.0
        if 8.0 <= hour <= 10.5:
            delta = hour - 8.2
            meal_effect = meal_spike_factor * math.exp(-(delta ** 2) / 0.8)
        elif 13.0 <= hour <= 15.5:
            delta = hour - 13.3
            meal_effect = (meal_spike_factor * 1.1) * math.exp(-(delta ** 2) / 1.0)
        elif 19.5 <= hour <= 22.5:
            delta = hour - 19.8
            # Marcus has a larger late-night dinner spike
            mult = 1.3 if persona_id == "marcus_metabolic" else 0.9
            meal_effect = (meal_spike_factor * mult) * math.exp(-(delta ** 2) / 1.2)

        # Micro-fluctuations and natural noise
        noise = random.uniform(-2.5, 2.5)
        glucose_val = fasting_base + dawn_effect + meal_effect + noise
        glucose_val = max(60.0, min(240.0, glucose_val))
        
        samples.append(GlucoseSample(
            timestamp=sample_time.strftime("%Y-%m-%dT%H:%M:%S"),
            glucose_mg_dl=round(glucose_val, 1)
        ))
    
    return samples


def generate_unified_profile(persona_id: str, date_str: Optional[str] = None) -> UnifiedHealthProfile:
    """Generate a full day's unified Terra profile for a given persona."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    cfg = PERSONAS.get(persona_id, PERSONAS["alex_longevity"])
    b = cfg["baseline"]
    
    # 1. Sleep payload
    if persona_id == "alex_longevity":
        sleep_hours = 7.9
        efficiency = 93.5
        deep_mins = 115
        rem_mins = 110
        light_mins = 230
        awake_mins = 25
        hrv = round(b["hrv_baseline"] + random.uniform(-4, 6), 1)
        lowest_hr = 49.0
        sleep_score = 91
    elif persona_id == "sarah_athlete":
        sleep_hours = 8.5
        efficiency = 94.0
        deep_mins = 130
        rem_mins = 125
        light_mins = 235
        awake_mins = 20
        hrv = round(b["hrv_baseline"] + random.uniform(-8, 8), 1)
        lowest_hr = 41.0
        sleep_score = 94
    elif persona_id == "marcus_metabolic":
        sleep_hours = 6.2
        efficiency = 78.0
        deep_mins = 45
        rem_mins = 55
        light_mins = 240
        awake_mins = 60
        hrv = round(b["hrv_baseline"] + random.uniform(-3, 3), 1)
        lowest_hr = 68.0
        sleep_score = 64
    else:  # elena_cognitive
        sleep_hours = 7.1
        efficiency = 87.0
        deep_mins = 85
        rem_mins = 95
        light_mins = 220
        awake_mins = 40
        hrv = round(b["hrv_baseline"] + random.uniform(-5, 5), 1)
        lowest_hr = 55.0
        sleep_score = 82

    sleep_payload = TerraSleepPayload(
        start_time=f"{date_str}T22:45:00",
        end_time=f"{date_str}T07:00:00",
        duration_total_seconds=int(sleep_hours * 3600),
        duration_asleep_seconds=int((deep_mins + rem_mins + light_mins) * 60),
        sleep_efficiency_pct=efficiency,
        sleep_score=sleep_score,
        stages=SleepStageDurations(
            deep_sleep_seconds=deep_mins * 60,
            rem_sleep_seconds=rem_mins * 60,
            light_sleep_seconds=light_mins * 60,
            awake_seconds=awake_mins * 60,
        ),
        avg_hrv_rmssd_ms=hrv,
        lowest_heart_rate_bpm=lowest_hr,
        respiratory_rate_rpm=14.2,
        temperature_deviation_c=random.uniform(-0.2, 0.2)
    )

    # 2. Daily payload
    if persona_id == "sarah_athlete":
        steps = 18450
        active_cal = 1250.0
        dist = 14500.0
    elif persona_id == "alex_longevity":
        steps = 11200
        active_cal = 620.0
        dist = 8200.0
    elif persona_id == "marcus_metabolic":
        steps = 4300
        active_cal = 280.0
        dist = 3100.0
    else:
        steps = 8900
        active_cal = 490.0
        dist = 6400.0

    daily_payload = TerraDailyPayload(
        timestamp=f"{date_str}T23:59:59",
        steps=steps,
        active_calories=active_cal,
        resting_calories=1750.0,
        distance_meters=dist,
        resting_heart_rate_bpm=b["resting_hr"],
        avg_heart_rate_bpm=b["resting_hr"] + 18.0,
        max_heart_rate_bpm=168.0 if persona_id == "sarah_athlete" else 145.0,
        floors_climbed=12,
        estimated_vo2_max=b["vo2_max"]
    )

    # 3. Activities
    activities = []
    if persona_id == "sarah_athlete":
        activities.append(TerraActivityPayload(
            activity_id="act_triathlon_run",
            activity_name="Zone 2 Aerobic Base Run",
            start_time=f"{date_str}T07:30:00",
            duration_seconds=3600,
            calories_burned=620.0,
            avg_hr_bpm=138.0,
            max_hr_bpm=155.0,
            hr_zones=HeartRateZones(
                zone1_minutes=10.0,
                zone2_minutes=42.0,
                zone3_minutes=8.0,
                zone4_minutes=0.0,
                zone5_minutes=0.0
            ),
            strain_score=14.8
        ))
    elif persona_id == "alex_longevity":
        activities.append(TerraActivityPayload(
            activity_id="act_zone2_longevity",
            activity_name="Mitochondrial Zone 2 Cycling",
            start_time=f"{date_str}T17:15:00",
            duration_seconds=2700,
            calories_burned=380.0,
            avg_hr_bpm=124.0,
            max_hr_bpm=136.0,
            hr_zones=HeartRateZones(
                zone1_minutes=5.0,
                zone2_minutes=35.0,
                zone3_minutes=5.0,
                zone4_minutes=0.0,
                zone5_minutes=0.0
            ),
            strain_score=10.4
        ))
    elif persona_id == "marcus_metabolic":
        activities.append(TerraActivityPayload(
            activity_id="act_walk_post_meal",
            activity_name="Post-Lunch Glucose Blunting Walk",
            start_time=f"{date_str}T13:45:00",
            duration_seconds=1200,
            calories_burned=95.0,
            avg_hr_bpm=102.0,
            max_hr_bpm=115.0,
            hr_zones=HeartRateZones(
                zone1_minutes=18.0,
                zone2_minutes=2.0,
                zone3_minutes=0.0,
                zone4_minutes=0.0,
                zone5_minutes=0.0
            ),
            strain_score=4.2
        ))
    else:
        activities.append(TerraActivityPayload(
            activity_id="act_flow_pilates",
            activity_name="Cognitive Reset Pilates & Mobility",
            start_time=f"{date_str}T12:30:00",
            duration_seconds=1800,
            calories_burned=140.0,
            avg_hr_bpm=108.0,
            max_hr_bpm=122.0,
            hr_zones=HeartRateZones(
                zone1_minutes=20.0,
                zone2_minutes=10.0,
                zone3_minutes=0.0,
                zone4_minutes=0.0,
                zone5_minutes=0.0
            ),
            strain_score=6.1
        ))

    # 4. Body & CGM payload
    cgm_samples = generate_cgm_series(persona_id, date_str)
    body_payload = TerraBodyPayload(
        timestamp=f"{date_str}T07:15:00",
        weight_kg=74.5 if persona_id in ["alex_longevity", "elena_cognitive"] else (62.0 if persona_id == "sarah_athlete" else 94.0),
        bmi=23.2 if persona_id != "marcus_metabolic" else 29.8,
        body_fat_pct=15.5 if persona_id == "alex_longevity" else (13.0 if persona_id == "sarah_athlete" else 28.5),
        blood_pressure_systolic=118 if persona_id != "marcus_metabolic" else 138,
        blood_pressure_diastolic=76 if persona_id != "marcus_metabolic" else 88,
        fasting_glucose_mg_dl=b["glucose_fasting"],
        cgm_readings_24h=cgm_samples
    )

    # 5. Recent behavioral logs (for causal graph analysis)
    behaviors = []
    if persona_id == "alex_longevity":
        behaviors = [
            {"behavior": "sauna_20min", "timing": "18:00", "impact_category": "positive"},
            {"behavior": "fasting_14h", "timing": "08:00", "impact_category": "positive"},
            {"behavior": "dinner_before_7pm", "timing": "18:45", "impact_category": "positive"}
        ]
    elif persona_id == "marcus_metabolic":
        behaviors = [
            {"behavior": "late_dinner_heavy_carbs", "timing": "21:30", "impact_category": "negative"},
            {"behavior": "screen_time_bed", "timing": "23:45", "impact_category": "negative"},
            {"behavior": "missed_morning_light", "timing": "09:00", "impact_category": "negative"}
        ]
    elif persona_id == "sarah_athlete":
        behaviors = [
            {"behavior": "tart_cherry_sleep", "timing": "21:00", "impact_category": "positive"},
            {"behavior": "ice_bath_recovery", "timing": "11:00", "impact_category": "neutral"},
            {"behavior": "electrolytes_supplement", "timing": "07:00", "impact_category": "positive"}
        ]
    else:
        behaviors = [
            {"behavior": "meditation_15min", "timing": "07:30", "impact_category": "positive"},
            {"behavior": "coffee_after_2pm", "timing": "15:30", "impact_category": "negative"}
        ]

    return UnifiedHealthProfile(
        user_id=f"terra_usr_{persona_id}",
        persona_id=persona_id,
        date=date_str,
        daily=daily_payload,
        sleep=sleep_payload,
        activities=activities,
        body=body_payload,
        recent_behaviors=behaviors
    )


def generate_longitudinal_series(persona_id: str, days: int = 14) -> List[UnifiedHealthProfile]:
    """Generate multi-day historical telemetry for trend & predictive modeling."""
    history = []
    now = datetime.now()
    for d in range(days, 0, -1):
        day_str = (now - timedelta(days=d)).strftime("%Y-%m-%d")
        profile = generate_unified_profile(persona_id, day_str)
        history.append(profile)
    return history
