"""
Statistically-fit anomaly detection, replacing the fixed absolute-margin
thresholds (e.g. "flag any HRV drop >= 15ms") previously hardcoded in
models/odin_ai.py. Those margins were applied identically to every persona
regardless of that persona's own day-to-day variability - a flat 15ms
threshold over-flags a low-variance persona and under-flags a high-variance
one.

Two layers, kept deliberately separate:

1. A per-persona, per-metric MAD control chart (Iglewicz & Hoaglin, 1993):
   modified_z = 0.6745 * (x - median) / MAD, flagged when |modified_z| > 3.5.
   This is the primary, live-scoring layer - cheap, explainable, and exactly
   the right tool for a handful of independent 1-D series.

2. An IsolationForest fit on rolling multi-metric features (rolling
   mean/std/rate-of-change across HRV, resting HR, sleep efficiency, plus
   day-of-week). This is a SECONDARY, offline/batch layer for catching
   correlated multi-metric drift (mild shifts across several metrics at
   once) that no single-metric chart would trip - it is intentionally not
   the primary detector: with only a few hundred daily points and a handful
   of features, IsolationForest as a primary method would be underpowered
   relative to a technique purpose-built for this shape of data.

See training/train_anomaly_baselines.py for how these are fit/persisted,
and training/reports/anomaly_detection_report.md for the evaluation this
produced against known injected events.
"""

from __future__ import annotations

import json
import os
import zlib
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence

import numpy as np

from data.longitudinal_simulator import (
    PERSONA_METRIC_PARAMS,
    InjectedEvent,
    SimulatedDay,
    TRACKED_METRICS,
    simulate_persona_history,
)

MAD_Z_THRESHOLD = 3.5  # Iglewicz & Hoaglin's recommended cutoff
MAD_SCALE_CONSTANT = 0.6745  # 0.75th-percentile of the standard normal

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
BASELINES_DIR = os.path.join(ARTIFACTS_DIR, "anomaly_baselines")
ISOLATION_FOREST_DIR = os.path.join(ARTIFACTS_DIR, "isolation_forest")


# ---------------------------------------------------------------------------
# MAD control chart
# ---------------------------------------------------------------------------

def compute_mad_baseline(values: Sequence[float]) -> Dict[str, float]:
    """Median + MAD of a series - the two numbers a persona's baseline is."""
    arr = np.asarray(values, dtype=float)
    median = float(np.median(arr))
    mad = float(np.median(np.abs(arr - median)))
    return {"median": median, "mad": mad}


def modified_z_score(value: float, median: float, mad: float) -> float:
    """
    Iglewicz & Hoaglin's modified z-score. If MAD is 0 (a degenerate,
    perfectly constant reference window), fall back to a hard equality
    check rather than dividing by zero.
    """
    if mad == 0.0:
        return 0.0 if value == median else float("inf")
    return MAD_SCALE_CONSTANT * (value - median) / mad


def compute_persona_baselines(series: List[SimulatedDay]) -> Dict[str, Dict[str, float]]:
    """
    Full-history median/MAD per tracked metric. MAD's robustness to
    outliers is exactly why this is safe to fit directly on a series that
    still contains the ~3% of days affected by injected events - a few
    illness days don't meaningfully move the median or MAD.
    """
    return {
        metric: compute_mad_baseline([getattr(day, metric) for day in series])
        for metric in TRACKED_METRICS
    }


def rolling_mad_flags(values: Sequence[float], window: int = 14) -> List[Optional[bool]]:
    """
    Trailing-window MAD flags: day i's flag uses only days [i-window, i),
    never the current day itself, so the detector never sees the future
    or leaks the point it's judging into its own reference stats. First
    `window` days have no flag (insufficient history) and are None.
    """
    flags: List[Optional[bool]] = []
    for i in range(len(values)):
        if i < window:
            flags.append(None)
            continue
        reference = values[i - window:i]
        baseline = compute_mad_baseline(reference)
        z = modified_z_score(values[i], baseline["median"], baseline["mad"])
        flags.append(abs(z) > MAD_Z_THRESHOLD)
    return flags


def save_persona_baselines(persona_id: str, baselines: Dict[str, Dict[str, float]]) -> str:
    os.makedirs(BASELINES_DIR, exist_ok=True)
    path = os.path.join(BASELINES_DIR, f"{persona_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(baselines, f, indent=2)
    return path


def load_persona_baselines(persona_id: str) -> Optional[Dict[str, Dict[str, float]]]:
    path = os.path.join(BASELINES_DIR, f"{persona_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def score_today(
    persona_id: str,
    hrv_rmssd_ms: float,
    resting_hr_bpm: float,
    sleep_efficiency_pct: float,
) -> Optional[Dict[str, Dict[str, float]]]:
    """
    Score a single day's observed values against a persona's persisted
    MAD baseline. Returns None if no baseline has been trained yet (see
    training/train_anomaly_baselines.py) so callers can fall back cleanly.
    """
    baselines = load_persona_baselines(persona_id)
    if baselines is None:
        return None
    observed = {
        "hrv_rmssd_ms": hrv_rmssd_ms,
        "resting_hr_bpm": resting_hr_bpm,
        "sleep_efficiency_pct": sleep_efficiency_pct,
    }
    result = {}
    for metric, value in observed.items():
        b = baselines[metric]
        z = modified_z_score(value, b["median"], b["mad"])
        result[metric] = {
            "value": value,
            "baseline_median": b["median"],
            "modified_z_score": round(z, 2),
            "is_anomalous": abs(z) > MAD_Z_THRESHOLD,
        }
    return result


# ---------------------------------------------------------------------------
# Legacy fixed-threshold replica (for the before/after evaluation only)
# ---------------------------------------------------------------------------

def legacy_fixed_threshold_flags(series: List[SimulatedDay], persona_id: str) -> List[bool]:
    """
    Replicates the pre-Phase-2 hardcoded logic in models/odin_ai.py:
    HRV drop >= 15ms or RHR rise >= 5bpm from the persona's single fixed
    baseline point, applied identically regardless of that persona's own
    variance. Used only as the "before" column in the evaluation report.
    """
    base_hrv = PERSONA_METRIC_PARAMS.get(persona_id, PERSONA_METRIC_PARAMS["alex_longevity"])["hrv_rmssd_ms"]["mu"]
    base_rhr = PERSONA_METRIC_PARAMS.get(persona_id, PERSONA_METRIC_PARAMS["alex_longevity"])["resting_hr_bpm"]["mu"]
    flags = []
    for day in series:
        hrv_flag = (base_hrv - day.hrv_rmssd_ms) >= 15.0
        rhr_flag = (day.resting_hr_bpm - base_rhr) >= 5.0
        flags.append(hrv_flag or rhr_flag)
    return flags


# ---------------------------------------------------------------------------
# Secondary layer: IsolationForest over rolling multivariate features
# ---------------------------------------------------------------------------

def build_rolling_features(series: List[SimulatedDay], window: int = 7) -> np.ndarray:
    """
    Rolling mean/std/rate-of-change per tracked metric plus day-of-week,
    for days with a full trailing window. Row i corresponds to series[i]
    for i >= window (earlier days have no feature row).
    """
    rows = []
    values_by_metric = {m: [getattr(d, m) for d in series] for m in TRACKED_METRICS}

    for i in range(window, len(series)):
        row: List[float] = []
        for metric in TRACKED_METRICS:
            window_vals = values_by_metric[metric][i - window:i]
            mean = float(np.mean(window_vals))
            std = float(np.std(window_vals))
            roc = values_by_metric[metric][i - 1] - values_by_metric[metric][i - window]
            row.extend([mean, std, roc])
        dow = datetime.strptime(series[i].date, "%Y-%m-%d").weekday()
        row.append(float(dow))
        rows.append(row)
    return np.array(rows, dtype=float)


@dataclass
class IsolationForestScanner:
    """Thin, explicit wrapper so callers don't need to know sklearn's API."""
    model: "object"  # sklearn.ensemble.IsolationForest, typed loosely to avoid a hard import at module load

    @classmethod
    def fit(cls, features: np.ndarray, contamination: float = 0.05, random_state: int = 42) -> "IsolationForestScanner":
        from sklearn.ensemble import IsolationForest
        model = IsolationForest(contamination=contamination, random_state=random_state, n_estimators=200)
        model.fit(features)
        return cls(model=model)

    def flags(self, features: np.ndarray) -> List[bool]:
        # sklearn convention: -1 = anomaly, 1 = normal
        predictions = self.model.predict(features)
        return [p == -1 for p in predictions]

    def save(self, path: str) -> None:
        import joblib
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump(self.model, path)

    @classmethod
    def load(cls, path: str) -> Optional["IsolationForestScanner"]:
        if not os.path.exists(path):
            return None
        import joblib
        return cls(model=joblib.load(path))


def isolation_forest_path(persona_id: str) -> str:
    return os.path.join(ISOLATION_FOREST_DIR, f"{persona_id}.joblib")


# ---------------------------------------------------------------------------
# Evaluation: score a detector's day-level flags against injected events
# ---------------------------------------------------------------------------

def evaluate_detector(
    flags: Sequence[Optional[bool]],
    events: List[InjectedEvent],
    num_days: int,
    buffer_days: int = 1,
) -> Dict[str, float]:
    """
    Event-level recall (fraction of injected events with >=1 flagged day
    within [start-buffer, end+buffer]), day-level precision/F1 (of days
    with a defined flag), and false positives per 30 days - the
    product-relevant "how many false alarms a month" metric.
    """
    in_event_window = [False] * num_days
    for event in events:
        lo = max(0, event.start_day - buffer_days)
        hi = min(num_days - 1, event.end_day + buffer_days)
        for d in range(lo, hi + 1):
            in_event_window[d] = True

    scored_days = [i for i, f in enumerate(flags) if f is not None]
    true_positive_days = sum(1 for i in scored_days if flags[i] and in_event_window[i])
    false_positive_days = sum(1 for i in scored_days if flags[i] and not in_event_window[i])
    false_negative_days = sum(1 for i in scored_days if (not flags[i]) and in_event_window[i])

    events_detected = 0
    for event in events:
        lo = max(0, event.start_day - buffer_days)
        hi = min(num_days - 1, event.end_day + buffer_days)
        if any(flags[d] for d in range(lo, hi + 1) if d in scored_days and flags[d]):
            events_detected += 1

    event_recall = events_detected / len(events) if events else float("nan")
    precision = (
        true_positive_days / (true_positive_days + false_positive_days)
        if (true_positive_days + false_positive_days) > 0 else float("nan")
    )
    recall = (
        true_positive_days / (true_positive_days + false_negative_days)
        if (true_positive_days + false_negative_days) > 0 else float("nan")
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision == precision and recall == recall and (precision + recall) > 0 else float("nan")
    )
    scored_span_days = len(scored_days)
    false_positives_per_30_days = (
        (false_positive_days / scored_span_days) * 30 if scored_span_days > 0 else float("nan")
    )

    return {
        "event_level_recall": round(event_recall, 3) if event_recall == event_recall else None,
        "day_level_precision": round(precision, 3) if precision == precision else None,
        "day_level_recall": round(recall, 3) if recall == recall else None,
        "day_level_f1": round(f1, 3) if f1 == f1 else None,
        "false_positives_per_30_days": round(false_positives_per_30_days, 2) if false_positives_per_30_days == false_positives_per_30_days else None,
        "num_events": len(events),
        "num_scored_days": scored_span_days,
    }


# ---------------------------------------------------------------------------
# Live demonstration: scan a trailing window with the full detector stack
# ---------------------------------------------------------------------------

# Matches training/train_anomaly_baselines.py's seeding convention exactly,
# so a live scan reproduces (a prefix of) the same series the evaluation
# report was scored against, rather than a fresh random history per request.
_SIMULATION_SEED_BASE = 20260904


def scan_persona_window(persona_id: str, days: int = 60) -> Dict[str, Any]:
    """
    Live demonstration of the full detector stack over a simulated trailing
    window: the MAD control chart (primary) plus the persisted
    IsolationForest (secondary, offline-fit multivariate layer) if one has
    been trained. Ground-truth injected events are included in the response
    so a caller can see exactly what the detectors did or didn't catch.
    """
    persona_seed = _SIMULATION_SEED_BASE + (zlib.crc32(persona_id.encode()) % 1000)
    series, _events = simulate_persona_history(persona_id, days=days, seed=persona_seed)

    mad_flags_by_metric = {
        metric: rolling_mad_flags([getattr(d, metric) for d in series], window=14)
        for metric in TRACKED_METRICS
    }

    scanner = IsolationForestScanner.load(isolation_forest_path(persona_id))
    if_flags_by_index: Dict[int, bool] = {}
    if scanner is not None and len(series) > 7:
        features = build_rolling_features(series, window=7)
        for j, flag in enumerate(scanner.flags(features)):
            if_flags_by_index[j + 7] = flag

    flagged_days = []
    for i, day in enumerate(series):
        mad_hit = any(bool(mad_flags_by_metric[m][i]) for m in TRACKED_METRICS if mad_flags_by_metric[m][i])
        if_hit = if_flags_by_index.get(i, False)
        if mad_hit or if_hit:
            flagged_days.append({
                "date": day.date,
                "day_index": day.day_index,
                "hrv_rmssd_ms": day.hrv_rmssd_ms,
                "resting_hr_bpm": day.resting_hr_bpm,
                "sleep_efficiency_pct": day.sleep_efficiency_pct,
                "ground_truth_event": day.active_event,
                "mad_flag": mad_hit,
                "isolation_forest_flag": bool(if_hit),
            })

    return {
        "persona_id": persona_id,
        "window_days": days,
        "isolation_forest_trained": scanner is not None,
        "num_days_scanned": len(series),
        "num_flagged_days": len(flagged_days),
        "flagged_days": flagged_days,
    }
