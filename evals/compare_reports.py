"""
Diffs two eval reports produced by evals/run_eval.py, producing the
concrete before/after table this project's "fine-tuning AI performance
metrics" story is built on: tweak prompts/odin_prompts.py, rerun
evals/run_eval.py, then diff the new report against the old one here.

Run with:
    python -m evals.compare_reports evals/reports/v1_....json evals/reports/v2_....json
or, to auto-find each version's most recent report:
    python -m evals.compare_reports --latest v1 v2
"""

from __future__ import annotations

import argparse
import glob
import json
import os
from typing import Any, Dict, Optional

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")
COMPARED_METRICS = ["numeric_grounding_rate", "citation_validity_rate", "scope_handling_rate"]


def find_latest_report(version: str) -> str:
    candidates = sorted(glob.glob(os.path.join(REPORTS_DIR, f"{version}_*.json")))
    if not candidates:
        raise FileNotFoundError(f"No eval reports found for prompt version '{version}' in {REPORTS_DIR}")
    return candidates[-1]


def load_report(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def diff_value(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None:
        return None
    return round(b - a, 3)


def compare(report_a: Dict[str, Any], report_b: Dict[str, Any]) -> Dict[str, Any]:
    overall_diff = {
        metric: {
            "before": report_a["overall"].get(metric),
            "after": report_b["overall"].get(metric),
            "delta": diff_value(report_a["overall"].get(metric), report_b["overall"].get(metric)),
        }
        for metric in COMPARED_METRICS + ["mean_latency_ms"]
    }

    categories = sorted(set(report_a["by_category"]) | set(report_b["by_category"]))
    category_diff = {}
    for cat in categories:
        a_cat = report_a["by_category"].get(cat, {})
        b_cat = report_b["by_category"].get(cat, {})
        category_diff[cat] = {
            metric: {
                "before": a_cat.get(metric),
                "after": b_cat.get(metric),
                "delta": diff_value(a_cat.get(metric), b_cat.get(metric)),
            }
            for metric in COMPARED_METRICS
        }

    return {
        "before_version": report_a["prompt_version"],
        "after_version": report_b["prompt_version"],
        "before_timestamp": report_a["timestamp"],
        "after_timestamp": report_b["timestamp"],
        "before_num_live_ai": report_a.get("num_live_ai", 0),
        "after_num_live_ai": report_b.get("num_live_ai", 0),
        "overall": overall_diff,
        "by_category": category_diff,
    }


def format_markdown(diff: Dict[str, Any]) -> str:
    lines = [
        f"# Eval Comparison: {diff['before_version']} -> {diff['after_version']}",
        "",
        f"Before: {diff['before_timestamp']} ({diff['before_num_live_ai']} live-AI responses) | "
        f"After: {diff['after_timestamp']} ({diff['after_num_live_ai']} live-AI responses)",
        "",
    ]
    if diff["before_num_live_ai"] == 0 and diff["after_num_live_ai"] == 0:
        lines.append(
            "**Note:** neither run had a live LLM API key configured, so both ran entirely against "
            "the deterministic fallback engine, which does not read the system prompt at all - this "
            "diff cannot show a genuine prompt-version effect. Rerun with `--api-key <your HF token>` "
            "on both prompt versions to get a real comparison."
        )
        lines.append("")
    lines.append("## Overall")
    lines.append("")
    lines.append("| Metric | Before | After | Delta |")
    lines.append("|---|---|---|---|")
    for metric, v in diff["overall"].items():
        lines.append(f"| {metric} | {v['before']} | {v['after']} | {v['delta']} |")
    lines.append("")
    lines.append("## By Category")
    for cat, metrics in diff["by_category"].items():
        lines.append(f"\n### {cat}\n")
        lines.append("| Metric | Before | After | Delta |")
        lines.append("|---|---|---|---|")
        for metric, v in metrics.items():
            lines.append(f"| {metric} | {v['before']} | {v['after']} | {v['delta']} |")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Compare two OdinAI eval reports.")
    parser.add_argument("before", help="Path to the 'before' report JSON, or a prompt version string with --latest")
    parser.add_argument("after", help="Path to the 'after' report JSON, or a prompt version string with --latest")
    parser.add_argument("--latest", action="store_true", help="Treat before/after as prompt version strings and auto-find each one's latest report")
    args = parser.parse_args()

    before_path = find_latest_report(args.before) if args.latest else args.before
    after_path = find_latest_report(args.after) if args.latest else args.after

    diff = compare(load_report(before_path), load_report(after_path))
    print(format_markdown(diff))


if __name__ == "__main__":
    main()
