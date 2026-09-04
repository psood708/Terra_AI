"""
Churn/retention risk model - logistic regression as the primary, shipped
model (appropriately sized and interpretable for a dataset of this scale;
its coefficients map directly to growth/retention talking points, e.g.
"a streak break raises churn odds by X%"). See training/train_churn_model.py
for the benchmarked-but-not-shipped HistGradientBoostingClassifier
comparison, both split strategies, and the honest metrics report -
including why the target AUC range is deliberately bounded (0.70-0.85),
not maximized: see data/engagement_simulator.py's module docstring.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List, Optional

import numpy as np

ARTIFACTS_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
CHURN_MODEL_PATH = os.path.join(ARTIFACTS_DIR, "churn_model.joblib")


@dataclass
class ChurnModel:
    pipeline: object  # sklearn Pipeline(StandardScaler, LogisticRegression)
    feature_columns: List[str]

    @classmethod
    def fit(cls, X: np.ndarray, y: np.ndarray, feature_columns: List[str], random_state: int = 42) -> "ChurnModel":
        from sklearn.linear_model import LogisticRegression
        from sklearn.pipeline import Pipeline
        from sklearn.preprocessing import StandardScaler

        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=random_state)),
        ])
        pipeline.fit(X, y)
        return cls(pipeline=pipeline, feature_columns=feature_columns)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return self.pipeline.predict_proba(X)[:, 1]

    def save(self, path: str = CHURN_MODEL_PATH) -> None:
        import joblib
        os.makedirs(os.path.dirname(path), exist_ok=True)
        joblib.dump({"pipeline": self.pipeline, "feature_columns": self.feature_columns}, path)

    @classmethod
    def load(cls, path: str = CHURN_MODEL_PATH) -> Optional["ChurnModel"]:
        if not os.path.exists(path):
            return None
        import joblib
        data = joblib.load(path)
        return cls(pipeline=data["pipeline"], feature_columns=data["feature_columns"])


def build_feature_vector(features: Dict[str, float], persona_id: str, feature_columns: List[str]) -> np.ndarray:
    from data.churn_dataset import FEATURE_NAMES
    row = []
    for col in feature_columns:
        if col in FEATURE_NAMES:
            row.append(features.get(col, 0.0))
        elif col.startswith("persona_"):
            row.append(1.0 if col == f"persona_{persona_id}" else 0.0)
        else:
            row.append(0.0)
    return np.array([row], dtype=float)


# ---------------------------------------------------------------------------
# Live estimation: no real per-user engagement history exists in this demo
# system (api/reward_routes.py only ever receives a persona_id and a raw
# streak_days integer, not a stored session log), so we score against one
# representative simulated individual per persona and pick the simulated
# day whose OWN streak length most closely matches the caller's - this
# keeps every feature internally consistent (all coming from one coherent
# trajectory) rather than splicing real and synthetic signals together.
# ---------------------------------------------------------------------------

@lru_cache(maxsize=8)
def _representative_individual_examples(persona_id: str):
    from data.churn_dataset import build_examples_for_individual
    from data.engagement_simulator import simulate_engagement
    from data.longitudinal_simulator import simulate_from_params
    from data.persona_archetypes import sample_population

    params = sample_population(persona_id, n_individuals=1, seed=20260904)[0]
    series, _events = simulate_from_params(params, days=180, seed=20260904)
    engagement = simulate_engagement(series, seed=20260905)
    # Dense cutoffs (stride=1) here since this is a small, one-off lookup,
    # not the bulk training dataset - we want the closest possible streak match.
    return build_examples_for_individual(persona_id, 0, series, engagement, cutoff_stride_days=1)


def estimate_live_churn_risk(persona_id: str, current_streak_days: int) -> Optional[Dict[str, float]]:
    """
    Returns {"churn_probability": ..., "matched_streak_length": ...} scored
    against the closest-matching day of a representative simulated
    individual, or None if no trained model artifact exists yet.
    """
    model = ChurnModel.load()
    if model is None:
        return None

    examples = _representative_individual_examples(persona_id)
    if not examples:
        return None

    best = min(examples, key=lambda ex: abs(ex.features["current_streak_length"] - current_streak_days))
    vector = build_feature_vector(best.features, persona_id, model.feature_columns)
    probability = float(model.predict_proba(vector)[0])
    return {
        "churn_probability": round(probability, 3),
        "matched_streak_length": best.features["current_streak_length"],
    }
