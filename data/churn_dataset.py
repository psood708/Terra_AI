"""
Builds the labeled churn-prediction dataset from the population,
physiological, and engagement simulators. Every feature is strictly
backward-looking from its cutoff day (day t only ever uses data from
[0, t]) - the label alone looks forward, into (t, t+CHURN_HORIZON_DAYS].

See data/engagement_simulator.py's module docstring for why the label
isn't a tautological inversion of the physiology-linked engagement signal.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from typing import Dict, List

import numpy as np

from data.engagement_simulator import (
    EngagementDay,
    compute_churn_labels,
    recovery_proxy_series,
    simulate_engagement,
)
from data.longitudinal_simulator import SimulatedDay, TRACKED_METRICS, simulate_from_params
from data.persona_archetypes import sample_population
from models.anomaly_detector import rolling_mad_flags

MIN_HISTORY_DAYS = 30
CHURN_HORIZON_DAYS = 30
CUTOFF_STRIDE_DAYS = 7
ANOMALY_WINDOW_DAYS = 14

FEATURE_NAMES = [
    "days_since_last_open",
    "opens_last_7d",
    "opens_last_14d",
    "opens_last_30d",
    "engagement_trend_delta",
    "current_streak_length",
    "streak_breaks_last_30d",
    "recovery_mean_last_14d",
    "recovery_std_last_14d",
    "anomaly_count_last_30d",
    "tenure_days",
]


@dataclass
class ChurnExample:
    persona_id: str
    individual_index: int
    cutoff_day: int
    features: Dict[str, float]
    label: bool
    # Raw cutoff-day physiological values + date, kept alongside the
    # engineered features so training/train_churn_model.py can construct a
    # real UnifiedHealthProfile and run the actual RewardOptimizer heuristic
    # for a true apples-to-apples baseline comparison, not an approximation.
    date: str
    hrv_rmssd_ms: float
    resting_hr_bpm: float
    sleep_efficiency_pct: float


def _persona_seed_offset(persona_id: str) -> int:
    return zlib.crc32(persona_id.encode()) % 100_000


def _combined_anomaly_flags(series: List[SimulatedDay], window: int = ANOMALY_WINDOW_DAYS) -> List[bool]:
    per_metric = {
        metric: rolling_mad_flags([getattr(d, metric) for d in series], window=window)
        for metric in TRACKED_METRICS
    }
    combined = []
    for i in range(len(series)):
        vals = [per_metric[m][i] for m in TRACKED_METRICS]
        combined.append(any(v for v in vals if v is not None))
    return combined


def build_examples_for_individual(
    persona_id: str,
    individual_index: int,
    series: List[SimulatedDay],
    engagement: List[EngagementDay],
    cutoff_stride_days: int = CUTOFF_STRIDE_DAYS,
) -> List[ChurnExample]:
    labels = compute_churn_labels(engagement, horizon_days=CHURN_HORIZON_DAYS)
    recovery = recovery_proxy_series(series)
    anomaly_flags = _combined_anomaly_flags(series)

    examples: List[ChurnExample] = []
    n = len(series)
    for t in range(MIN_HISTORY_DAYS, n, cutoff_stride_days):
        if labels[t] is None:
            continue

        days_since_last_open = t + 1
        for back in range(0, t + 1):
            if engagement[t - back].app_opened:
                days_since_last_open = back
                break

        opens_7 = sum(1 for d in engagement[max(0, t - 6):t + 1] if d.app_opened)
        opens_14 = sum(1 for d in engagement[max(0, t - 13):t + 1] if d.app_opened)
        opens_30 = sum(1 for d in engagement[max(0, t - 29):t + 1] if d.app_opened)
        opens_prior14 = sum(1 for d in engagement[max(0, t - 27):max(0, t - 13)] if d.app_opened)
        engagement_trend_delta = opens_14 - opens_prior14

        streak_breaks_30 = sum(1 for d in engagement[max(0, t - 29):t + 1] if d.streak_broke_today)

        recovery_window = recovery[max(0, t - 13):t + 1]
        anomaly_window = anomaly_flags[max(0, t - 29):t + 1]

        features = {
            "days_since_last_open": float(days_since_last_open),
            "opens_last_7d": float(opens_7),
            "opens_last_14d": float(opens_14),
            "opens_last_30d": float(opens_30),
            "engagement_trend_delta": float(engagement_trend_delta),
            "current_streak_length": float(engagement[t].streak_length),
            "streak_breaks_last_30d": float(streak_breaks_30),
            "recovery_mean_last_14d": float(np.mean(recovery_window)),
            "recovery_std_last_14d": float(np.std(recovery_window)),
            "anomaly_count_last_30d": float(sum(anomaly_window)),
            "tenure_days": float(t),
        }
        examples.append(ChurnExample(
            persona_id=persona_id,
            individual_index=individual_index,
            cutoff_day=t,
            features=features,
            label=bool(labels[t]),
            date=series[t].date,
            hrv_rmssd_ms=series[t].hrv_rmssd_ms,
            resting_hr_bpm=series[t].resting_hr_bpm,
            sleep_efficiency_pct=series[t].sleep_efficiency_pct,
        ))
    return examples


def build_dataset(
    persona_ids: List[str],
    n_individuals_per_persona: int = 40,
    days: int = 240,
    seed: int = 20260904,
) -> List[ChurnExample]:
    all_examples: List[ChurnExample] = []
    for persona_id in persona_ids:
        offset = _persona_seed_offset(persona_id)
        population_params = sample_population(persona_id, n_individuals_per_persona, seed=seed + offset)
        for idx, params in enumerate(population_params):
            individual_seed = seed + offset + idx * 7919
            series, _events = simulate_from_params(params, days=days, seed=individual_seed)
            engagement = simulate_engagement(series, seed=individual_seed + 1)
            all_examples.extend(build_examples_for_individual(persona_id, idx, series, engagement))
    return all_examples


def to_feature_matrix(examples: List[ChurnExample], persona_ids: List[str]):
    """
    Dense numpy feature matrix + label vector, with persona_id one-hot
    columns appended last (so callers can slice them off for the
    with/without-persona-id ablation described in training/train_churn_model.py).
    """
    rows = []
    labels = []
    for ex in examples:
        row = [ex.features[name] for name in FEATURE_NAMES]
        row.extend(1.0 if ex.persona_id == pid else 0.0 for pid in persona_ids)
        rows.append(row)
        labels.append(1.0 if ex.label else 0.0)
    feature_columns = FEATURE_NAMES + [f"persona_{pid}" for pid in persona_ids]
    return np.array(rows, dtype=float), np.array(labels, dtype=float), feature_columns
