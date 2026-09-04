"""
Deterministic eval harness for OdinAI's query responses (models/odin_ai.py).
This is the concrete, re-runnable answer to "testing AI models" / "fine-
tuning AI performance metrics": run the golden set, tweak a prompt version
in prompts/odin_prompts.py, rerun, and evals/compare_reports.py shows the
diff between two timestamped reports.

Deterministic checks are the backbone, not an LLM judge:
  - Numeric grounding: does the response reference at least one real
    number from the persona's actual telemetry (within tolerance)?
  - Citation validity: does every citation the response returns actually
    exist in data/citations_corpus.json? (A structural regression guard -
    directly motivated by finding a fabricated citation baked into this
    project's original code before Phase 4.)
  - Scope handling: for out-of-scope/missing-data queries, does the
    response avoid fabricating a specific number for data it doesn't have?
  - Latency: measured and reported, never hard-gated (real API latency is
    genuinely variable).

A small, explicitly SECONDARY LLM-as-judge tier is available (run with
--llm-judge) but only runs if an API key is configured; it is directional
scoring, not part of the core pass/fail harness - see run_llm_judge().

Run with: python -m evals.run_eval [--api-key KEY] [--provider huggingface] [--llm-judge]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data.mock_generator import generate_unified_profile  # noqa: E402
from models.citation_retriever import load_corpus  # noqa: E402
from models.odin_ai import OdinAIEngine  # noqa: E402
from prompts.odin_prompts import PROMPT_VERSION  # noqa: E402

GOLDEN_QUERIES_PATH = os.path.join(os.path.dirname(__file__), "golden_queries.json")
REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")

NUMBER_PATTERN = re.compile(r"-?\d+\.?\d*")


def load_golden_queries() -> List[Dict[str, Any]]:
    with open(GOLDEN_QUERIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_numbers(text: str) -> List[float]:
    return [float(n) for n in NUMBER_PATTERN.findall(text)]


def expected_value_for_metric(engine: OdinAIEngine, profile, metric: Optional[str]) -> Optional[float]:
    """Independently recomputes the ground-truth value a grounded response should reference."""
    if metric is None:
        return None
    if metric == "recovery_score":
        return engine.analyze_recovery_status(profile)["recovery_score"]
    if metric == "avg_glucose":
        cgm = profile.body.cgm_readings_24h or []
        if not cgm:
            return profile.body.fasting_glucose_mg_dl
        return round(sum(g.glucose_mg_dl for g in cgm) / len(cgm), 1)
    raise ValueError(f"Unknown grounding_metric: {metric}")


def check_numeric_grounding(response_text: str, expected_value: Optional[float], tolerance: float = 1.0) -> Optional[bool]:
    """None if there was nothing to ground against (grounding_metric was null for this query)."""
    if expected_value is None:
        return None
    found_numbers = extract_numbers(response_text)
    return any(abs(found - expected_value) <= tolerance for found in found_numbers)


def check_citation_validity(returned_citations: List[Dict[str, str]], corpus_titles: set) -> Optional[bool]:
    """None if no citations were returned at all (nothing to check)."""
    if not returned_citations:
        return None
    return all(c.get("title") in corpus_titles for c in returned_citations)


# Fields the fallback/live engine has no data source for at all - if a
# response confidently reports a specific number here, that's a fabrication.
_OUT_OF_SCOPE_LEAK_PATTERNS = [
    re.compile(r"\b\d+\s*(?:°|degrees)\s*[FC]\b", re.IGNORECASE),  # a specific temperature
    re.compile(r"\bblood pressure\b.*?\b\d{2,3}\s*/\s*\d{2,3}\b", re.IGNORECASE),  # a specific BP reading
]


def check_scope_handling(category: str, response_text: str) -> Optional[bool]:
    """None if this isn't an out-of-scope/missing-data query (nothing to check)."""
    if category not in ("out_of_scope", "missing_data"):
        return None
    return not any(p.search(response_text) for p in _OUT_OF_SCOPE_LEAK_PATTERNS)


async def run_single_query(
    engine: OdinAIEngine,
    corpus_titles: set,
    query_spec: Dict[str, Any],
    api_key: Optional[str],
    provider: str,
) -> Dict[str, Any]:
    profile = generate_unified_profile(query_spec["persona_id"])
    expected_value = expected_value_for_metric(engine, profile, query_spec["grounding_metric"])

    start = time.perf_counter()
    result = await engine.process_query(
        query_text=query_spec["query"], profile=profile, api_key=api_key, provider=provider
    )
    latency_ms = (time.perf_counter() - start) * 1000.0

    grounding_ok = check_numeric_grounding(result["odin_response"], expected_value)
    citations_ok = check_citation_validity(result.get("scientific_citations", []), corpus_titles)
    scope_ok = check_scope_handling(query_spec["category"], result["odin_response"])

    return {
        "id": query_spec["id"],
        "persona_id": query_spec["persona_id"],
        "category": query_spec["category"],
        "is_live_ai": result["is_live_ai"],
        "latency_ms": round(latency_ms, 1),
        "numeric_grounding_ok": grounding_ok,
        "citation_validity_ok": citations_ok,
        "scope_handling_ok": scope_ok,
        "num_citations_returned": len(result.get("scientific_citations", [])),
    }


async def run_llm_judge(engine: OdinAIEngine, api_key: str, provider: str, sample_size: int = 8) -> Dict[str, Any]:
    """
    Explicitly secondary/directional tier: asks the LLM itself to rate a
    small sample of its own responses 1-5 on groundedness/helpfulness.
    Known judge variance/bias means this is reported separately from the
    deterministic results and never gates pass/fail.
    """
    queries = load_golden_queries()[:sample_size]
    scores = []
    for spec in queries:
        profile = generate_unified_profile(spec["persona_id"])
        result = await engine.process_query(query_text=spec["query"], profile=profile, api_key=api_key, provider=provider)
        if not result["is_live_ai"]:
            continue  # nothing to judge if we fell back to the heuristic engine
        judge_prompt = (
            "Rate the following health-assistant response on a 1-5 scale for groundedness "
            "(does it use the specific numbers it was given) and helpfulness. "
            f"Query: {spec['query']}\nResponse: {result['odin_response']}\n"
            "Reply with ONLY a single integer 1-5."
        )
        judge_response_text, _model, _err = await engine.generate_llm_response(
            query_text=judge_prompt, profile=profile, api_key=api_key, provider=provider
        )
        if judge_response_text:
            match = re.search(r"[1-5]", judge_response_text)
            if match:
                scores.append(int(match.group()))
    if not scores:
        return {"status": "skipped", "reason": "no live judge scores obtained"}
    return {"status": "ok", "sample_size": len(scores), "mean_score": round(sum(scores) / len(scores), 2), "scores": scores}


def rate_for(results: List[Dict[str, Any]], key: str) -> Optional[float]:
    scored = [r[key] for r in results if r[key] is not None]
    return round(sum(scored) / len(scored), 3) if scored else None


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    by_category: Dict[str, List[Dict[str, Any]]] = {}
    for r in results:
        by_category.setdefault(r["category"], []).append(r)
    category_summary = {
        cat: {
            "num_queries": len(rs),
            "numeric_grounding_rate": rate_for(rs, "numeric_grounding_ok"),
            "citation_validity_rate": rate_for(rs, "citation_validity_ok"),
            "scope_handling_rate": rate_for(rs, "scope_handling_ok"),
            "mean_latency_ms": round(sum(r["latency_ms"] for r in rs) / len(rs), 1),
        }
        for cat, rs in by_category.items()
    }

    return {
        "prompt_version": PROMPT_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "num_queries": len(results),
        "num_live_ai": sum(1 for r in results if r["is_live_ai"]),
        "overall": {
            "numeric_grounding_rate": rate_for(results, "numeric_grounding_ok"),
            "citation_validity_rate": rate_for(results, "citation_validity_ok"),
            "scope_handling_rate": rate_for(results, "scope_handling_ok"),
            "mean_latency_ms": round(sum(r["latency_ms"] for r in results) / len(results), 1),
        },
        "by_category": category_summary,
    }


async def main_async(api_key: Optional[str], provider: str, run_judge: bool) -> None:
    os.makedirs(REPORTS_DIR, exist_ok=True)
    engine = OdinAIEngine()
    corpus_titles = {c.title for c in load_corpus()}
    queries = load_golden_queries()

    results = [await run_single_query(engine, corpus_titles, q, api_key, provider) for q in queries]
    report = summarize(results)
    report["per_query_results"] = results

    if run_judge:
        if api_key:
            report["llm_judge"] = await run_llm_judge(engine, api_key, provider)
        else:
            report["llm_judge"] = {"status": "skipped", "reason": "no API key configured"}

    timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = os.path.join(REPORTS_DIR, f"{PROMPT_VERSION}_{timestamp_slug}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Wrote {json_path}")
    print(json.dumps({k: v for k, v in report.items() if k != "per_query_results"}, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Run the OdinAI deterministic eval harness.")
    parser.add_argument("--api-key", default=os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN"))
    parser.add_argument("--provider", default="huggingface")
    parser.add_argument("--llm-judge", action="store_true", help="Also run the small, secondary LLM-as-judge tier.")
    args = parser.parse_args()
    asyncio.run(main_async(args.api_key, args.provider, args.llm_judge))


if __name__ == "__main__":
    main()
