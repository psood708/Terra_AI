"""
Configuration and Domain Constants for Terra Intelligence Engine (TIE).
"""

import os
from typing import Dict, Any, List

# Automatically load environment variables from .env file if present
_env_file = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_file):
    try:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip("'\""))
    except Exception:
        pass

APP_NAME = "Terra Intelligence Engine"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = (
    "Production-grade Health Intelligence Layer built on top of Terra's unified "
    "wearable and sensor data infrastructure. Powers OdinAI reasoning, Terra Graph API "
    "visualizations, longitudinal bio-age forecasting, and behavioral retention optimization."
)

# Reference physiological ranges based on peer-reviewed clinical benchmarks
BIOMARKER_BENCHMARKS = {
    "hrv_rmssd_ms": {
        "poor": 30.0,
        "normal": 55.0,
        "optimal": 85.0,
        "elite": 110.0
    },
    "resting_hr_bpm": {
        "optimal": 50,
        "normal": 65,
        "elevated": 75,
        "high": 85
    },
    "sleep_efficiency_pct": {
        "poor": 75.0,
        "fair": 85.0,
        "optimal": 92.0
    },
    "glucose_tir_pct": {  # Time in Range (70-140 mg/dL)
        "poor": 60.0,
        "acceptable": 70.0,
        "optimal": 85.0,
        "elite": 95.0
    },
    "deep_sleep_pct": {
        "low": 12.0,
        "optimal": 20.0,
        "high": 25.0
    }
}

# Supported user personas matching Terra's mission
PERSONAS: Dict[str, Dict[str, Any]] = {
    "alex_longevity": {
        "id": "alex_longevity",
        "name": "Alex Vance",
        "age": 42,
        "target_goal": "Longevity & Lifespan (Target 120)",
        "objective": "Decelerate biological aging, optimize mitochondrial efficiency, maximize HRV resilience.",
        "primary_sensors": ["Oura Gen3", "Dexcom G7 CGM", "Apple Watch Ultra"],
        "baseline": {
            "resting_hr": 54,
            "hrv_baseline": 68.0,
            "vo2_max": 48.5,
            "chronological_age": 42,
            "biological_age": 38.2,
            "avg_sleep_hours": 7.8,
            "glucose_fasting": 84.0,
            "time_in_range_pct": 92.0
        }
    },
    "sarah_athlete": {
        "id": "sarah_athlete",
        "name": "Sarah Chen",
        "age": 27,
        "target_goal": "Olympic Triathlon Preparation",
        "objective": "Maximize peak power output, polarized 80/20 training, prevent overtraining syndrome.",
        "primary_sensors": ["WHOOP 4.0", "Garmin Forerunner 965", "Wahoo TICKR X"],
        "baseline": {
            "resting_hr": 43,
            "hrv_baseline": 96.0,
            "vo2_max": 62.0,
            "chronological_age": 27,
            "biological_age": 23.4,
            "avg_sleep_hours": 8.4,
            "glucose_fasting": 88.0,
            "time_in_range_pct": 96.0
        }
    },
    "marcus_metabolic": {
        "id": "marcus_metabolic",
        "name": "Marcus Sterling",
        "age": 49,
        "target_goal": "Metabolic Optimization & Pre-diabetes Reversal",
        "objective": "Flatten post-prandial glucose excursions, increase daily NEAT steps, reverse visceral adiposity.",
        "primary_sensors": ["Abbott FreeStyle Libre 3", "Fitbit Charge 6", "Withings Body Scan"],
        "baseline": {
            "resting_hr": 74,
            "hrv_baseline": 36.0,
            "vo2_max": 33.0,
            "chronological_age": 49,
            "biological_age": 53.6,
            "avg_sleep_hours": 6.3,
            "glucose_fasting": 118.0,
            "time_in_range_pct": 68.0
        }
    },
    "elena_cognitive": {
        "id": "elena_cognitive",
        "name": "Elena Rostova",
        "age": 34,
        "target_goal": "Cognitive Edge & Executive Stamina",
        "objective": "Maximize deep restorative sleep, stabilize autonomic nervous system during stress spikes.",
        "primary_sensors": ["Eight Sleep Pod 4", "Oura Ring Gen3", "Apollo Neuro"],
        "baseline": {
            "resting_hr": 58,
            "hrv_baseline": 62.0,
            "vo2_max": 44.0,
            "chronological_age": 34,
            "biological_age": 32.8,
            "avg_sleep_hours": 7.1,
            "glucose_fasting": 90.0,
            "time_in_range_pct": 88.0
        }
    }
}
