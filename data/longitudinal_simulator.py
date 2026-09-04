"""
Richer longitudinal telemetry simulator with autocorrelated day-to-day
variation and injected physiological events (illness/travel/overtraining/
alcohol). Feeds the offline training/evaluation of models/anomaly_detector.py
and, later, the churn model in data/engagement_simulator.py.

Deliberately kept separate from data/mock_generator.py: that module drives
the LIVE single-day API responses that the existing test suite depends on
verbatim, and is left untouched. This module only ever runs offline
(training scripts, evaluation), generating the kind of multi-month history
no single-day generator can provide - in particular, real day-to-day
variance for resting heart rate, which mock_generator.py sets to a fixed,
noise-free value.

Design notes (see docs/ML_DESIGN.md once Phase 8 lands):
  - Each tracked metric follows an AR(1) process: x_t = mu_t + phi*(x_{t-1}
    - mu_t) + eps_t, eps_t ~ N(0, sigma^2*(1-phi^2)) so the *stationary*
    variance of the series is exactly sigma^2 regardless of phi.
  - mu_t drifts slowly per persona (e.g. Marcus's metabolic markers
    improving under a "Terra-guided" narrative) so a rolling-window
    detector has something a single global baseline cannot adapt to.
  - Life events are injected at a small daily hazard, each shifting the
    metric means multiplicatively for the acute window then decaying
    linearly back to baseline - this event log is the ground truth used
    to score the anomaly detector, since no real labeled data exists.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

TRACKED_METRICS: Tuple[str, str, str] = ("hrv_rmssd_ms", "resting_hr_bpm", "sleep_efficiency_pct")

# Per-persona AR(1) parameters. sigma/phi are chosen to roughly match the
# variability data/mock_generator.py already implies for HRV, and to add
# realistic variance to resting_hr and sleep_efficiency, which that module
# treats as noise-free or persona-fixed.
PERSONA_METRIC_PARAMS: Dict[str, Dict[str, Dict[str, float]]] = {
    "alex_longevity": {
        "hrv_rmssd_ms": {"mu": 68.0, "sigma": 3.0, "phi": 0.4, "drift_per_day": 0.01},
        "resting_hr_bpm": {"mu": 54.0, "sigma": 1.8, "phi": 0.4, "drift_per_day": -0.005},
        "sleep_efficiency_pct": {"mu": 93.5, "sigma": 2.5, "phi": 0.3, "drift_per_day": 0.0},
    },
    "sarah_athlete": {
        "hrv_rmssd_ms": {"mu": 96.0, "sigma": 5.0, "phi": 0.4, "drift_per_day": 0.0},
        "resting_hr_bpm": {"mu": 43.0, "sigma": 1.5, "phi": 0.4, "drift_per_day": 0.0},
        "sleep_efficiency_pct": {"mu": 94.0, "sigma": 2.0, "phi": 0.3, "drift_per_day": 0.0},
    },
    "marcus_metabolic": {
        "hrv_rmssd_ms": {"mu": 36.0, "sigma": 2.2, "phi": 0.5, "drift_per_day": 0.015},
        "resting_hr_bpm": {"mu": 74.0, "sigma": 2.2, "phi": 0.5, "drift_per_day": -0.01},
        "sleep_efficiency_pct": {"mu": 78.0, "sigma": 4.5, "phi": 0.35, "drift_per_day": 0.01},
    },
    "elena_cognitive": {
        "hrv_rmssd_ms": {"mu": 62.0, "sigma": 3.5, "phi": 0.4, "drift_per_day": 0.0},
        "resting_hr_bpm": {"mu": 58.0, "sigma": 2.0, "phi": 0.4, "drift_per_day": 0.0},
        "sleep_efficiency_pct": {"mu": 87.0, "sigma": 3.5, "phi": 0.3, "drift_per_day": 0.0},
    },
}

# Documented, persona-agnostic event effects: percentage shift applied to
# that day's underlying AR(1) mean while the event is active.
EVENT_EFFECTS: Dict[str, Dict[str, float]] = {
    "illness":      {"hrv_pct": -0.30, "rhr_pct": +0.15, "sleep_eff_pct": -0.10},
    "travel":       {"hrv_pct": -0.12, "rhr_pct": +0.08, "sleep_eff_pct": -0.15},
    "overtraining": {"hrv_pct": -0.20, "rhr_pct": +0.10, "sleep_eff_pct": -0.05},
    "alcohol":      {"hrv_pct": -0.15, "rhr_pct": +0.05, "sleep_eff_pct": -0.08},
}
_METRIC_TO_PCT_KEY = {
    "hrv_rmssd_ms": "hrv_pct",
    "resting_hr_bpm": "rhr_pct",
    "sleep_efficiency_pct": "sleep_eff_pct",
}
DAILY_EVENT_HAZARD = 0.03
MIN_EVENT_DURATION_DAYS = 1
MAX_EVENT_DURATION_DAYS = 4
RECOVERY_DAYS = 2


@dataclass
class SimulatedDay:
    day_index: int
    date: str
    hrv_rmssd_ms: float
    resting_hr_bpm: float
    sleep_efficiency_pct: float
    active_event: Optional[str] = None


@dataclass
class InjectedEvent:
    event_type: str
    start_day: int
    duration_days: int
    end_day: int  # last day intensity is still > 0 (inclusive)


def simulate_persona_history(
    persona_id: str,
    days: int = 180,
    seed: Optional[int] = None,
    start_date: Optional[datetime] = None,
) -> Tuple[List[SimulatedDay], List[InjectedEvent]]:
    """
    Simulate `days` of autocorrelated daily telemetry for one of the four
    fixed personas. Thin wrapper around simulate_from_params() using that
    persona's own central parameters - see simulate_from_params() for the
    version driven by per-individual sampled parameters (data/persona_archetypes.py),
    needed to build a real population for the churn model in Phase 3.
    """
    params = PERSONA_METRIC_PARAMS.get(persona_id, PERSONA_METRIC_PARAMS["alex_longevity"])
    return simulate_from_params(params, days=days, seed=seed, start_date=start_date)


def simulate_from_params(
    params: Dict[str, Dict[str, float]],
    days: int = 180,
    seed: Optional[int] = None,
    start_date: Optional[datetime] = None,
) -> Tuple[List[SimulatedDay], List[InjectedEvent]]:
    """
    Core simulation engine, parameterized directly rather than looked up by
    persona_id - lets data/persona_archetypes.py drive many distinct
    synthetic individuals through the same generative process.
    """
    rng = random.Random(seed)
    start_date = start_date or (datetime.now() - timedelta(days=days))

    state = {m: params[m]["mu"] for m in TRACKED_METRICS}

    events: List[InjectedEvent] = []
    active_event: Optional[InjectedEvent] = None
    series: List[SimulatedDay] = []

    for day_index in range(days):
        date = (start_date + timedelta(days=day_index)).strftime("%Y-%m-%d")

        if active_event is None and rng.random() < DAILY_EVENT_HAZARD:
            event_type = rng.choice(list(EVENT_EFFECTS.keys()))
            duration = rng.randint(MIN_EVENT_DURATION_DAYS, MAX_EVENT_DURATION_DAYS)
            active_event = InjectedEvent(
                event_type=event_type,
                start_day=day_index,
                duration_days=duration,
                end_day=day_index + duration + RECOVERY_DAYS - 1,
            )
            events.append(active_event)

        intensity = 0.0
        event_label: Optional[str] = None
        if active_event is not None:
            elapsed = day_index - active_event.start_day
            if elapsed < active_event.duration_days:
                intensity = 1.0
            else:
                recovery_elapsed = elapsed - active_event.duration_days
                intensity = max(0.0, 1.0 - (recovery_elapsed + 1) / RECOVERY_DAYS)
            event_label = active_event.event_type
            if day_index >= active_event.end_day:
                active_event = None

        day_values: Dict[str, float] = {}
        for metric in TRACKED_METRICS:
            p = params[metric]
            mu_t = p["mu"] + p["drift_per_day"] * day_index
            innovation = rng.gauss(0.0, p["sigma"] * (1 - p["phi"] ** 2) ** 0.5)
            state[metric] = mu_t + p["phi"] * (state[metric] - mu_t) + innovation

            value = state[metric]
            if intensity > 0.0 and event_label is not None:
                pct_shift = EVENT_EFFECTS[event_label][_METRIC_TO_PCT_KEY[metric]] * intensity
                value = value * (1.0 + pct_shift)
            day_values[metric] = round(value, 2)

        series.append(SimulatedDay(
            day_index=day_index,
            date=date,
            hrv_rmssd_ms=day_values["hrv_rmssd_ms"],
            resting_hr_bpm=day_values["resting_hr_bpm"],
            sleep_efficiency_pct=day_values["sleep_efficiency_pct"],
            active_event=event_label,
        ))

    return series, events
