"""
Engagement/session simulator - the piece needed to train a churn model that
has no analog anywhere else in this codebase (there is no session or
engagement concept elsewhere; api/reward_routes.py takes streak_days as a
raw request parameter rather than deriving it from any stored history).

Habit strength H_t is a bounded random walk, reinforced weakly by how good
a day the individual's own physiology says it was (relative to THEIR OWN
history, not the shared persona baseline) and by continuing a streak, and
eroded by constant habit decay plus an INDEPENDENT idiosyncratic shock
(travel, a busy week, boredom - unrelated to physiology). That independent
term is a deliberate design choice, not an afterthought: if engagement
were driven only by the physiology-linked terms, a churn model would just
learn to invert this file's own formula and score a suspicious ~0.99 AUC.
Making the independent term comparable in magnitude to the physiology-
linked terms keeps physiological signals correlated with, but not
determinative of, churn - see training/train_churn_model.py's report for
the resulting (deliberately bounded) AUC and why that's the honest result.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional

from data.longitudinal_simulator import SimulatedDay, TRACKED_METRICS
from models.anomaly_detector import compute_mad_baseline, modified_z_score

BASE_HABIT_DECAY = 0.015
RECOVERY_BOOST_WEIGHT = 0.05
STREAK_BOOST_WEIGHT = 0.03
STREAK_BREAK_PENALTY = 0.04
RANDOM_WALK_NOISE_STD = 0.02
INITIAL_HABIT_STRENGTH = 0.6

# The idiosyncratic "life disruption" term is itself an AR(1) process, not
# i.i.d. daily noise: a busy season, an injury, or travel has DURATION, not
# just a single bad day. High phi_shock gives it a ~1/(1-phi) ~= 20-day
# memory, so it can occasionally erode habit_strength for long enough to
# produce a genuine 30-day silence (churn) - the actual churn horizon this
# is trained against. An i.i.d. shock was tried first and, empirically,
# never produced a gap longer than ~12 days across a 240-day series: with
# no persistence, a "bad day" is immediately washed out by mean reversion
# before it can compound into real disengagement.
SHOCK_PHI = 0.95
SHOCK_INNOVATION_STD = 0.05  # stationary std ~= 0.05 / sqrt(1-0.95^2) ~= 0.16


@dataclass
class EngagementDay:
    day_index: int
    date: str
    habit_strength: float
    app_opened: bool
    streak_length: int
    streak_broke_today: bool


def recovery_proxy_series(series: List[SimulatedDay]) -> List[float]:
    """
    Composite z-score of each day's HRV/RHR/sleep-efficiency against this
    INDIVIDUAL's own full-history median/MAD (not the shared per-persona
    baseline from models/anomaly_detector.py's persisted artifacts) - "did
    I have a good day, for me" is what plausibly drives whether someone
    opens a health app, not an absolute clinical threshold. Shared with
    data/churn_dataset.py so feature engineering uses the exact same
    computation the engagement simulator itself was driven by.
    """
    baselines = {m: compute_mad_baseline([getattr(d, m) for d in series]) for m in TRACKED_METRICS}
    proxies = []
    for day in series:
        hrv_z = modified_z_score(day.hrv_rmssd_ms, **baselines["hrv_rmssd_ms"])
        rhr_z = modified_z_score(day.resting_hr_bpm, **baselines["resting_hr_bpm"])
        sleep_z = modified_z_score(day.sleep_efficiency_pct, **baselines["sleep_efficiency_pct"])
        composite = 0.5 * hrv_z - 0.3 * rhr_z + 0.2 * sleep_z
        proxies.append(max(-3.0, min(3.0, composite)))  # clip so one extreme day can't dominate
    return proxies


def simulate_engagement(series: List[SimulatedDay], seed: Optional[int] = None) -> List[EngagementDay]:
    rng = random.Random(seed)
    recovery = recovery_proxy_series(series)

    habit_strength = INITIAL_HABIT_STRENGTH
    streak_length = 0
    shock_state = 0.0
    engagement: List[EngagementDay] = []

    for i, day in enumerate(series):
        recovery_term = RECOVERY_BOOST_WEIGHT * (recovery[i] / 3.0)
        streak_term = STREAK_BOOST_WEIGHT * min(1.0, streak_length / 14.0)
        noise = rng.gauss(0.0, RANDOM_WALK_NOISE_STD)

        shock_state = SHOCK_PHI * shock_state + rng.gauss(0.0, SHOCK_INNOVATION_STD)

        habit_strength = (
            habit_strength - BASE_HABIT_DECAY + recovery_term + streak_term
            - shock_state + noise
        )
        habit_strength = max(0.0, min(1.0, habit_strength))

        app_opened = rng.random() < habit_strength
        streak_broke_today = (streak_length > 0) and (not app_opened)
        if app_opened:
            streak_length += 1
        else:
            streak_length = 0
            if streak_broke_today:
                habit_strength = max(0.0, habit_strength - STREAK_BREAK_PENALTY)

        engagement.append(EngagementDay(
            day_index=day.day_index,
            date=day.date,
            habit_strength=round(habit_strength, 4),
            app_opened=app_opened,
            streak_length=streak_length,
            streak_broke_today=streak_broke_today,
        ))

    return engagement


def compute_churn_labels(engagement: List[EngagementDay], horizon_days: int = 30) -> List[Optional[bool]]:
    """
    churn_t = True if no app_opened in (t, t+horizon_days]. None where the
    full future horizon isn't available (the trailing horizon_days of the
    series) - those days simply can't be labeled and must be excluded from
    training, never treated as "not churned".
    """
    n = len(engagement)
    labels: List[Optional[bool]] = []
    for t in range(n):
        if t + horizon_days >= n:
            labels.append(None)
            continue
        future_window = engagement[t + 1: t + 1 + horizon_days]
        opened_again = any(d.app_opened for d in future_window)
        labels.append(not opened_again)
    return labels
