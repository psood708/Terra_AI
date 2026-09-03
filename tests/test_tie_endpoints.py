"""
Test Suite for Terra Intelligence Engine (TIE).
Verifies all API routes, OdinAI reasoning, Graph API, Trajectory & Retention models.
"""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Verify health check endpoint and subsystem status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "alex_longevity" in data["connected_personas"]
    assert data["subsystems"]["odin_ai_reasoning"] == "operational"
    assert data["subsystems"]["terra_graph_api"] == "operational"


def test_dashboard_root():
    """Verify root endpoint serves interactive HTML dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "TERRA" in response.text


def test_odin_query():
    """Verify OdinAI natural language reasoning with scientific citations."""
    payload = {
        "persona_id": "alex_longevity",
        "query": "Why is my recovery score at this level today and what should I do?"
    }
    response = client.post("/api/odin/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "recovery_score" in data["recovery_synthesis"]
    assert len(data["scientific_citations"]) > 0
    assert "Buchheit" in str(data["scientific_citations"])


def test_odin_recovery_endpoint():
    """Verify recovery endpoint returns HRV z-score and breakdown."""
    response = client.get("/api/odin/recovery/sarah_athlete")
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["recovery_score"] <= 100
    assert "hrv_z_score" in data["biometric_breakdown"]


def test_odin_anomalies_detection():
    """Verify anomaly detection catches metabolic/sleep issues in Marcus."""
    response = client.get("/api/odin/anomalies/marcus_metabolic")
    assert response.status_code == 200
    data = response.json()
    assert data["persona_id"] == "marcus_metabolic"
    assert data["anomalies_count"] >= 1


def test_graph_agp():
    """Verify Ambulatory Glucose Profile (AGP) endpoint."""
    response = client.get("/api/graph/agp/alex_longevity")
    assert response.status_code == 200
    data = response.json()
    assert data["chart_type"] == "ambulatory_glucose_profile"
    assert len(data["time_series"]["glucose_values"]) == 144
    assert 0 <= data["agp_metrics"]["time_in_range_pct"] <= 100


def test_graph_hypnogram():
    """Verify Sleep Hypnogram stage breakdown."""
    response = client.get("/api/graph/hypnogram/elena_cognitive")
    assert response.status_code == 200
    data = response.json()
    assert "deep" in data["stage_breakdown_minutes"]
    assert "rem" in data["stage_breakdown_minutes"]
    assert 0 <= data["efficiency_pct"] <= 100


def test_graph_knowledge_and_twins():
    """Verify causal knowledge graph and digital twin cohort matching."""
    kg_res = client.get("/api/graph/knowledge")
    assert kg_res.status_code == 200
    kg_data = kg_res.json()
    assert len(kg_data["nodes"]) > 5
    assert len(kg_data["edges"]) > 5

    twins_res = client.get("/api/graph/digital-twins/alex_longevity")
    assert twins_res.status_code == 200
    twins_data = twins_res.json()
    assert len(twins_data["digital_twins"]) > 0
    assert twins_data["digital_twins"][0]["similarity_score_pct"] > 50.0


def test_health_bio_age_and_what_if():
    """Verify biological age calculation and counterfactual simulation."""
    bio_res = client.get("/api/health-score/bio-age/alex_longevity")
    assert bio_res.status_code == 200
    bio_data = bio_res.json()
    assert bio_data["chronological_age"] == 42
    assert "biological_age" in bio_data

    whatif_payload = {
        "persona_id": "alex_longevity",
        "added_sleep_minutes": 30,
        "added_zone2_minutes_weekly": 60,
        "earlier_dinner_shift_hours": 2.0,
        "improved_glucose_tir_pct": 10.0
    }
    whatif_res = client.post("/api/health-score/what-if", json=whatif_payload)
    assert whatif_res.status_code == 200
    whatif_data = whatif_res.json()
    assert whatif_data["simulated_outcome"]["net_biological_years_saved"] > 0


def test_rewards_and_streak():
    """Verify retention rewards and streak claiming."""
    rewards_res = client.get("/api/rewards/alex_longevity?streak_days=10")
    assert rewards_res.status_code == 200
    rewards_data = rewards_res.json()
    assert rewards_data["daily_points_earned"] > 0
    assert "retention_index_score" in rewards_data["retention_analytics"]

    claim_res = client.post("/api/rewards/claim-streak", json={
        "persona_id": "alex_longevity",
        "current_streak_days": 10
    })
    assert claim_res.status_code == 200
    claim_data = claim_res.json()
    assert claim_data["streak_claimed"] is True
    assert claim_data["new_streak_days"] == 11


def test_webhook_ingestion():
    """Verify Terra webhook simulation endpoint."""
    webhook_payload = {
        "event_id": "evt_test_9999",
        "event_type": "daily",
        "user_id": "terra_usr_alex",
        "timestamp": "2026-09-03T12:00:00Z",
        "data": {
            "steps": 10450,
            "resting_hr": 52,
            "active_calories": 580.0
        }
    }
    res = client.post("/api/webhooks/terra", json=webhook_payload)
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_odin_query_with_api_params():
    """Verify OdinAI handles provider and api_key parameters gracefully."""
    payload = {
        "persona_id": "alex_longevity",
        "query": "How do I optimize deep sleep tonight?",
        "api_key": "test_invalid_dummy_key",
        "provider": "gemini"
    }
    response = client.post("/api/odin/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "odin_response" in data
    assert "is_live_ai" in data


def test_test_connection_endpoint():
    """Verify test-connection endpoint returns diagnostic json."""
    payload = {
        "api_key": "test_invalid_key",
        "provider": "gemini"
    }
    response = client.post("/api/odin/test-connection", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
