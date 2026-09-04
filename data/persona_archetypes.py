"""
Reframes each of the four fixed personas in data/longitudinal_simulator.py's
PERSONA_METRIC_PARAMS as a DISTRIBUTION over individuals, not a single fixed
trajectory. Needed because a churn/retention model trained on n=4
trajectories (one per persona) has no real population to learn from or
split into train/test - see training/train_churn_model.py.

Individual baseline means are sampled around each persona's central value;
sigma/phi are lightly jittered too (people sharing a persona archetype
still differ somewhat in their own day-to-day variability and momentum),
while drift_per_day is kept at the persona's own value since it encodes a
narrative choice (e.g. Marcus improving under guided intervention) rather
than a per-individual trait.
"""

from __future__ import annotations

import random
from typing import Dict, List

from data.longitudinal_simulator import PERSONA_METRIC_PARAMS, TRACKED_METRICS

# Between-subject standard deviation as a multiple of the persona's own
# (within-subject, day-to-day) sigma - two people sharing an archetype
# plausibly differ from each other by somewhat more than either differs
# from themselves day to day.
BETWEEN_SUBJECT_SD_MULTIPLIER = 1.5


def sample_individual_params(persona_id: str, rng: random.Random) -> Dict[str, Dict[str, float]]:
    """One synthetic individual's AR(1) parameters, drawn around the persona's own."""
    persona_params = PERSONA_METRIC_PARAMS.get(persona_id, PERSONA_METRIC_PARAMS["alex_longevity"])
    individual: Dict[str, Dict[str, float]] = {}
    for metric in TRACKED_METRICS:
        p = persona_params[metric]
        between_subject_sd = p["sigma"] * BETWEEN_SUBJECT_SD_MULTIPLIER
        individual[metric] = {
            "mu": p["mu"] + rng.gauss(0.0, between_subject_sd),
            "sigma": max(0.5, p["sigma"] * rng.uniform(0.8, 1.2)),
            "phi": min(0.8, max(0.1, p["phi"] * rng.uniform(0.9, 1.1))),
            "drift_per_day": p["drift_per_day"],
        }
    return individual


def sample_population(
    persona_id: str, n_individuals: int, seed: int
) -> List[Dict[str, Dict[str, float]]]:
    """n_individuals independently sampled parameter sets for one persona archetype."""
    rng = random.Random(seed)
    return [sample_individual_params(persona_id, rng) for _ in range(n_individuals)]
