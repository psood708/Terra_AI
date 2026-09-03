"""
Unit tests for models/anomaly_detector.py and data/longitudinal_simulator.py -
independent of the FastAPI layer, asserting the actual statistics rather
than just "the endpoint returns 200".
"""

from fastapi.testclient import TestClient

from data.longitudinal_simulator import simulate_persona_history
from main import app
from models.anomaly_detector import (
    build_rolling_features,
    compute_mad_baseline,
    evaluate_detector,
    modified_z_score,
    rolling_mad_flags,
)

client = TestClient(app)


def test_mad_baseline_and_z_score_flag_known_outlier():
    # 20 stable points around 50, one clear outlier at index 10.
    values = [50.0] * 20
    values[10] = 90.0
    baseline = compute_mad_baseline(values)
    assert baseline["median"] == 50.0

    z_outlier = modified_z_score(90.0, baseline["median"], baseline["mad"])
    z_normal = modified_z_score(50.0, baseline["median"], baseline["mad"])
    assert abs(z_outlier) > 3.5
    assert abs(z_normal) <= 3.5


def test_modified_z_score_handles_zero_mad():
    # A perfectly constant reference window has MAD == 0; must not divide by zero.
    assert modified_z_score(10.0, median=10.0, mad=0.0) == 0.0
    assert modified_z_score(15.0, median=10.0, mad=0.0) == float("inf")


def test_rolling_mad_flags_no_lookahead_and_catches_injected_spike():
    window = 14
    series = [50.0] * 40
    series[25] = 120.0  # sharp, isolated spike well past the warm-up window

    flags = rolling_mad_flags(series, window=window)

    # No history yet for the first `window` days.
    assert all(f is None for f in flags[:window])
    # The spike itself is flagged...
    assert flags[25] is True
    # ...but a stable day far from the spike is not.
    assert flags[35] is False


def test_evaluate_detector_perfect_vs_noisy():
    num_days = 30
    from data.longitudinal_simulator import InjectedEvent

    event = InjectedEvent(event_type="illness", start_day=10, duration_days=3, end_day=14)

    perfect_flags = [False] * num_days
    for d in range(event.start_day, event.end_day + 1):
        perfect_flags[d] = True
    perfect_result = evaluate_detector(perfect_flags, [event], num_days, buffer_days=0)
    assert perfect_result["event_level_recall"] == 1.0
    assert perfect_result["day_level_precision"] == 1.0
    assert perfect_result["false_positives_per_30_days"] == 0.0

    never_flags = [False] * num_days
    never_result = evaluate_detector(never_flags, [event], num_days, buffer_days=0)
    assert never_result["event_level_recall"] == 0.0


def test_simulate_persona_history_is_reproducible_and_seed_sensitive():
    series_a, events_a = simulate_persona_history("marcus_metabolic", days=60, seed=42)
    series_b, events_b = simulate_persona_history("marcus_metabolic", days=60, seed=42)
    series_c, _ = simulate_persona_history("marcus_metabolic", days=60, seed=43)

    assert [d.hrv_rmssd_ms for d in series_a] == [d.hrv_rmssd_ms for d in series_b]
    assert len(events_a) == len(events_b)
    assert [d.hrv_rmssd_ms for d in series_a] != [d.hrv_rmssd_ms for d in series_c]


def test_build_rolling_features_shape():
    series, _ = simulate_persona_history("alex_longevity", days=50, seed=1)
    window = 7
    features = build_rolling_features(series, window=window)
    assert features.shape[0] == 50 - window
    assert features.shape[1] == 3 * 3 + 1  # 3 metrics x (mean,std,roc) + day-of-week


def test_scan_endpoint_returns_flagged_days_with_ground_truth():
    response = client.get("/api/odin/anomalies/marcus_metabolic/scan?days=60")
    assert response.status_code == 200
    data = response.json()
    assert data["persona_id"] == "marcus_metabolic"
    assert data["num_days_scanned"] == 60
    assert "flagged_days" in data
    for day in data["flagged_days"]:
        assert "mad_flag" in day and "isolation_forest_flag" in day
