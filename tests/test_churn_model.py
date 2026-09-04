"""
Unit tests for data/engagement_simulator.py, data/churn_dataset.py, and
models/churn_model.py. Deliberately does NOT depend on
models/artifacts/churn_model.joblib existing (it's gitignored and only
produced by training/train_churn_model.py) - tests that touch the live
estimate helper accept either a trained or untrained state.
"""

from fastapi.testclient import TestClient

from data.churn_dataset import (
    FEATURE_NAMES,
    build_dataset,
    build_examples_for_individual,
    to_feature_matrix,
)
from data.engagement_simulator import EngagementDay, compute_churn_labels, simulate_engagement
from data.longitudinal_simulator import simulate_persona_history
from main import app
from models.churn_model import ChurnModel, estimate_live_churn_risk

client = TestClient(app)


def _toy_engagement(pattern: list) -> list:
    """Builds a minimal EngagementDay list from a list of bools (app_opened)."""
    days = []
    streak = 0
    for i, opened in enumerate(pattern):
        broke = streak > 0 and not opened
        streak = streak + 1 if opened else 0
        days.append(EngagementDay(
            day_index=i, date=f"2026-01-{i + 1:02d}", habit_strength=0.5,
            app_opened=opened, streak_length=streak, streak_broke_today=broke,
        ))
    return days


def test_compute_churn_labels_no_lookahead_and_correct_direction():
    # 40 days: opens every day except a 35-day silent stretch starting day 5.
    pattern = [True] * 5 + [False] * 35
    engagement = _toy_engagement(pattern)
    labels = compute_churn_labels(engagement, horizon_days=30)

    # Last 30 days can't be labeled (no full future horizon available).
    assert all(l is None for l in labels[-30:])
    # Day 4 (last open before the long silence) should be labeled True:
    # no open occurs in the 30 days after it.
    assert labels[4] is True
    # Day 0 has opens on days 1-4 within its 30-day future window, so False.
    assert labels[0] is False


def test_simulate_engagement_stays_in_bounds_and_varies():
    series, _events = simulate_persona_history("marcus_metabolic", days=180, seed=7)
    engagement = simulate_engagement(series, seed=7)
    assert len(engagement) == len(series)
    assert all(0.0 <= d.habit_strength <= 1.0 for d in engagement)
    opens = sum(d.app_opened for d in engagement)
    assert 0 < opens < len(engagement)  # neither "never opens" nor "always opens"


def test_build_examples_for_individual_feature_correctness():
    # build_examples_for_individual only emits rows for cutoff days >= 30
    # (needs 30 days of prior history) with a full 30-day future label
    # window remaining - so the "interesting" hand-crafted week has to sit
    # right before a cutoff day that satisfies both, not at the very start.
    # 28 warm-up opens, then a 7-day interesting week at days 28-34
    # ([T,T,F,T,F,F,T]), then 61 more days so day 34's label is computable.
    pattern = [True] * 28 + [True, True, False, True, False, False, True] + [True] * 61
    engagement = _toy_engagement(pattern)
    series, _events = simulate_persona_history("alex_longevity", days=len(engagement), seed=1)

    examples = build_examples_for_individual("alex_longevity", 0, series, engagement, cutoff_stride_days=1)
    by_day = {ex.cutoff_day: ex for ex in examples}

    # Day 34: last 7 days are indices 28-34 = [T,T,F,T,F,F,T] -> opens_last_7d == 4.
    assert by_day[34].features["opens_last_7d"] == 4.0
    # Day 34 opened today after day 33 (closed) reset the streak -> streak_length == 1.
    assert by_day[34].features["current_streak_length"] == 1.0
    # days_since_last_open at day 34 is 0 (opened today).
    assert by_day[34].features["days_since_last_open"] == 0.0
    # Day 33: closed; last open was day 31 -> days_since_last_open == 2.
    assert by_day[33].features["days_since_last_open"] == 2.0


def test_build_dataset_and_feature_matrix_shapes():
    persona_ids = ["alex_longevity", "sarah_athlete"]
    examples = build_dataset(persona_ids, n_individuals_per_persona=2, days=100, seed=1)
    assert len(examples) > 0
    assert {ex.persona_id for ex in examples} <= set(persona_ids)

    X, y, columns = to_feature_matrix(examples, persona_ids)
    assert X.shape[0] == len(examples)
    assert X.shape[1] == len(FEATURE_NAMES) + len(persona_ids)
    assert set(y.tolist()) <= {0.0, 1.0}
    assert columns[:len(FEATURE_NAMES)] == FEATURE_NAMES


def test_churn_model_fit_predict_save_load_roundtrip(tmp_path):
    import numpy as np

    rng = np.random.RandomState(0)
    X = rng.rand(200, 3)
    y = (X[:, 0] > 0.5).astype(float)  # a learnable, non-degenerate signal
    columns = ["a", "b", "c"]

    model = ChurnModel.fit(X, y, columns)
    probs = model.predict_proba(X)
    assert probs.shape == (200,)
    assert ((probs >= 0.0) & (probs <= 1.0)).all()

    save_path = str(tmp_path / "churn_model_test.joblib")
    model.save(save_path)
    loaded = ChurnModel.load(save_path)
    assert loaded is not None
    reloaded_probs = loaded.predict_proba(X)
    assert (probs == reloaded_probs).all()

    assert ChurnModel.load(str(tmp_path / "does_not_exist.joblib")) is None


def test_estimate_live_churn_risk_handles_trained_and_untrained_gracefully():
    result = estimate_live_churn_risk("marcus_metabolic", current_streak_days=10)
    if result is not None:
        assert 0.0 <= result["churn_probability"] <= 1.0
        assert "matched_streak_length" in result
    # If None, the model simply hasn't been trained in this environment yet -
    # both outcomes are valid depending on whether training has run.


def test_rewards_endpoint_includes_ml_model_fields():
    response = client.get("/api/rewards/marcus_metabolic?streak_days=5")
    assert response.status_code == 200
    analytics = response.json()["retention_analytics"]
    assert "ml_model_churn_probability" in analytics
    assert "ml_model_note" in analytics
    if analytics["ml_model_churn_probability"] is not None:
        assert 0.0 <= analytics["ml_model_churn_probability"] <= 1.0
