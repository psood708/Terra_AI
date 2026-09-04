"""
Unit tests for evals/run_eval.py and evals/compare_reports.py - the eval
harness's own logic needs to be correct independent of whether a live LLM
API key is available in the environment running the tests.
"""

import asyncio

from data.mock_generator import generate_unified_profile
from evals.compare_reports import compare, diff_value
from evals.run_eval import (
    check_citation_validity,
    check_numeric_grounding,
    check_scope_handling,
    expected_value_for_metric,
    extract_numbers,
    rate_for,
    run_single_query,
)
from models.citation_retriever import load_corpus
from models.odin_ai import OdinAIEngine


def test_extract_numbers():
    assert extract_numbers("Your HRV is 62.5 ms and RHR is 54 bpm.") == [62.5, 54.0]
    assert extract_numbers("No numbers here.") == []


def test_check_numeric_grounding_within_and_outside_tolerance():
    assert check_numeric_grounding("Your recovery score is 72.3/100 today.", expected_value=72.5, tolerance=1.0) is True
    assert check_numeric_grounding("Your recovery score is 40.0/100 today.", expected_value=72.5, tolerance=1.0) is False
    assert check_numeric_grounding("Nothing to ground here.", expected_value=None) is None


def test_check_citation_validity():
    real_titles = {c.title for c in load_corpus()}
    real_citation = next(iter(load_corpus()))
    valid = [{"title": real_citation.title}]
    invalid = [{"title": "A Completely Fabricated Paper That Does Not Exist"}]

    assert check_citation_validity(valid, real_titles) is True
    assert check_citation_validity(invalid, real_titles) is False
    assert check_citation_validity([], real_titles) is None


def test_check_scope_handling_catches_fabricated_values():
    assert check_scope_handling("out_of_scope", "It's 72°F and sunny today.") is False
    assert check_scope_handling("out_of_scope", "I don't have weather data - I can help with your biometrics.") is True
    assert check_scope_handling("missing_data", "Your blood pressure was 120/80 last week.") is False
    assert check_scope_handling("direct_metric", "Whatever text, not checked for this category.") is None


def test_expected_value_for_metric_matches_engine_output():
    engine = OdinAIEngine()
    profile = generate_unified_profile("alex_longevity")
    recovery_score = expected_value_for_metric(engine, profile, "recovery_score")
    assert recovery_score == engine.analyze_recovery_status(profile)["recovery_score"]
    assert expected_value_for_metric(engine, profile, None) is None


def test_run_single_query_shape_and_grounding():
    engine = OdinAIEngine()
    corpus_titles = {c.title for c in load_corpus()}
    query_spec = {
        "id": "test_query",
        "persona_id": "alex_longevity",
        "category": "direct_metric",
        "query": "Why is my recovery score at this level today?",
        "grounding_metric": "recovery_score",
        "expects_citation": True,
    }
    result = asyncio.run(run_single_query(engine, corpus_titles, query_spec, api_key=None, provider="huggingface"))
    assert result["id"] == "test_query"
    assert result["numeric_grounding_ok"] is True
    assert result["citation_validity_ok"] is True
    assert result["latency_ms"] >= 0.0


def test_rate_for_ignores_none_values():
    results = [{"k": True}, {"k": False}, {"k": None}]
    assert rate_for(results, "k") == 0.5


def test_compare_reports_computes_deltas():
    report_a = {
        "prompt_version": "v1", "timestamp": "t0", "num_live_ai": 0,
        "overall": {"numeric_grounding_rate": 0.5, "citation_validity_rate": 1.0, "scope_handling_rate": 1.0, "mean_latency_ms": 10.0},
        "by_category": {"direct_metric": {"numeric_grounding_rate": 0.5, "citation_validity_rate": 1.0, "scope_handling_rate": None}},
    }
    report_b = {
        "prompt_version": "v2", "timestamp": "t1", "num_live_ai": 0,
        "overall": {"numeric_grounding_rate": 0.8, "citation_validity_rate": 1.0, "scope_handling_rate": 1.0, "mean_latency_ms": 12.0},
        "by_category": {"direct_metric": {"numeric_grounding_rate": 0.8, "citation_validity_rate": 1.0, "scope_handling_rate": None}},
    }
    diff = compare(report_a, report_b)
    assert diff["overall"]["numeric_grounding_rate"]["delta"] == 0.3
    assert diff["by_category"]["direct_metric"]["numeric_grounding_rate"]["delta"] == 0.3
    assert diff_value(None, 5.0) is None
