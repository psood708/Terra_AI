"""
Builds the churn dataset, trains the primary logistic-regression churn
model (benchmarked against a HistGradientBoostingClassifier and against
the ACTUAL existing RewardOptimizer heuristic - not an approximation of
it), and writes an honest evaluation report.

Run with: python -m training.train_churn_model

Writes:
  - models/artifacts/churn_model.joblib (gitignored - regenerate via this script)
  - training/reports/churn_model_report.{md,json}
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np  # noqa: E402
from sklearn.metrics import (  # noqa: E402
    average_precision_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)

from config import PERSONAS  # noqa: E402
from data.churn_dataset import FEATURE_NAMES, build_dataset, to_feature_matrix  # noqa: E402
from data.mock_generator import generate_unified_profile  # noqa: E402
from models.churn_model import ChurnModel  # noqa: E402
from models.reward_optimizer import RewardOptimizer  # noqa: E402

PERSONA_IDS = list(PERSONAS.keys())
N_INDIVIDUALS_PER_PERSONA = 40
SIMULATION_DAYS = 240
DATASET_SEED = 20260904
TEMPORAL_SPLIT_FRACTION = 0.7
TOP_RISK_FRACTION = 0.2  # "flag the top 20% highest-risk" operating point

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "reports")


def temporal_split_mask(examples, train_fraction: float = TEMPORAL_SPLIT_FRACTION):
    """
    Global cutoff-day threshold applied uniformly across all individuals:
    "train on each individual's first ~70% of days, test on the final 30%"
    without leaking any individual's later days into training.
    """
    cutoff_days = sorted({ex.cutoff_day for ex in examples})
    split_index = int(len(cutoff_days) * train_fraction)
    threshold = cutoff_days[split_index]
    train_mask = np.array([ex.cutoff_day < threshold for ex in examples])
    return train_mask, threshold


def evaluate_scores(y_true: np.ndarray, scores: np.ndarray) -> dict:
    """scores can be probabilities OR any ranking-consistent score (AUC only needs the ranking)."""
    if len(set(y_true.tolist())) < 2:
        return {"error": "degenerate test split - only one class present"}
    roc_auc = roc_auc_score(y_true, scores)
    pr_auc = average_precision_score(y_true, scores)

    k = max(1, int(len(scores) * TOP_RISK_FRACTION))
    top_k_idx = np.argsort(-scores)[:k]
    predicted = np.zeros_like(y_true)
    predicted[top_k_idx] = 1

    return {
        "roc_auc": round(float(roc_auc), 3),
        "pr_auc": round(float(pr_auc), 3),
        f"precision_at_top_{int(TOP_RISK_FRACTION * 100)}pct": round(float(precision_score(y_true, predicted, zero_division=0)), 3),
        f"recall_at_top_{int(TOP_RISK_FRACTION * 100)}pct": round(float(recall_score(y_true, predicted, zero_division=0)), 3),
        f"f1_at_top_{int(TOP_RISK_FRACTION * 100)}pct": round(float(f1_score(y_true, predicted, zero_division=0)), 3),
    }


def evaluate_calibration(y_true: np.ndarray, probabilities: np.ndarray) -> dict:
    return {"brier_score": round(float(brier_score_loss(y_true, probabilities)), 4)}


_CHURN_RISK_ORDINAL = {"Low": 1, "Moderate": 2, "High": 3}


def _churn_risk_ordinal(churn_risk_level: str) -> int:
    for key, value in _CHURN_RISK_ORDINAL.items():
        if churn_risk_level.startswith(key):
            return value
    return 1


def existing_heuristic_scores(examples) -> np.ndarray:
    """
    Runs the ACTUAL, unmodified RewardOptimizer.compute_daily_rewards() -
    not a re-implementation of its logic - by constructing a real
    UnifiedHealthProfile per example (generate_unified_profile() as the
    persona-level template for steps/CGM/activity, with the three fields
    this project's richer simulator actually models - HRV, resting HR,
    sleep efficiency - overridden to that example's simulated values).
    Returns an ordinal Low/Moderate/High -> 1/2/3 score per example (valid
    for AUC, which only depends on ranking, not the actual heuristic's
    completion-ratio bucketing having ever been probability-calibrated).
    """
    optimizer = RewardOptimizer()
    scores = []
    for ex in examples:
        profile = generate_unified_profile(ex.persona_id, ex.date)
        profile.sleep = profile.sleep.model_copy(update={
            "avg_hrv_rmssd_ms": ex.hrv_rmssd_ms,
            "sleep_efficiency_pct": ex.sleep_efficiency_pct,
        })
        profile.daily = profile.daily.model_copy(update={
            "resting_heart_rate_bpm": ex.resting_hr_bpm,
        })
        result = optimizer.compute_daily_rewards(profile, current_streak_days=max(1, int(ex.features["current_streak_length"])))
        scores.append(_churn_risk_ordinal(result["retention_analytics"]["churn_risk_level"]))
    return np.array(scores, dtype=float)


def main():
    os.makedirs(REPORTS_DIR, exist_ok=True)

    print(f"Building dataset: {N_INDIVIDUALS_PER_PERSONA} individuals/persona x {len(PERSONA_IDS)} personas, {SIMULATION_DAYS} days each...")
    examples = build_dataset(PERSONA_IDS, n_individuals_per_persona=N_INDIVIDUALS_PER_PERSONA, days=SIMULATION_DAYS, seed=DATASET_SEED)
    print(f"Built {len(examples)} examples. Positive (churn) rate: {sum(e.label for e in examples) / len(examples):.3f}")

    X, y, feature_columns = to_feature_matrix(examples, PERSONA_IDS)
    train_mask, threshold = temporal_split_mask(examples)
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[~train_mask], y[~train_mask]
    print(f"Temporal split at cutoff_day={threshold}: {train_mask.sum()} train / {(~train_mask).sum()} test")

    # --- Primary: logistic regression (shipped model) ---
    logreg = ChurnModel.fit(X_train, y_train, feature_columns)
    logreg_probs = logreg.predict_proba(X_test)
    logreg_metrics = evaluate_scores(y_test, logreg_probs)
    logreg_metrics.update(evaluate_calibration(y_test, logreg_probs))
    logreg.save()

    # --- Secondary: HistGradientBoosting (benchmarked, not shipped) ---
    from sklearn.ensemble import HistGradientBoostingClassifier
    hgb = HistGradientBoostingClassifier(random_state=42)
    hgb.fit(X_train, y_train)
    hgb_probs = hgb.predict_proba(X_test)[:, 1]
    hgb_metrics = evaluate_scores(y_test, hgb_probs)
    hgb_metrics.update(evaluate_calibration(y_test, hgb_probs))

    # --- Baseline: the actual existing RewardOptimizer heuristic ---
    test_examples = [ex for ex, keep in zip(examples, ~train_mask) if keep]
    heuristic_scores = existing_heuristic_scores(test_examples)
    heuristic_metrics = evaluate_scores(y_test, heuristic_scores)

    # --- Ablation: leave-one-persona-out generalization (no persona one-hot) ---
    X_no_persona = X[:, :len(FEATURE_NAMES)]
    persona_ids_array = np.array([ex.persona_id for ex in examples])
    loo_results = {}
    for held_out in PERSONA_IDS:
        train_idx = persona_ids_array != held_out
        test_idx = persona_ids_array == held_out
        model = ChurnModel.fit(X_no_persona[train_idx], y[train_idx], FEATURE_NAMES)
        probs = model.predict_proba(X_no_persona[test_idx])
        loo_results[held_out] = evaluate_scores(y[test_idx], probs)

    report = {
        "dataset": {
            "num_examples": len(examples),
            "positive_rate": round(float(y.mean()), 3),
            "num_individuals_per_persona": N_INDIVIDUALS_PER_PERSONA,
            "simulation_days": SIMULATION_DAYS,
            "temporal_split_cutoff_day": threshold,
            "num_train": int(train_mask.sum()),
            "num_test": int((~train_mask).sum()),
        },
        "temporal_holdout": {
            "logistic_regression": logreg_metrics,
            "hist_gradient_boosting": hgb_metrics,
            "existing_reward_optimizer_heuristic": heuristic_metrics,
        },
        "leave_one_persona_out": loo_results,
    }

    json_path = os.path.join(REPORTS_DIR, "churn_model_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    md_path = os.path.join(REPORTS_DIR, "churn_model_report.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(format_markdown_report(report))

    print(f"\nWrote {json_path}")
    print(f"Wrote {md_path}")
    print(json.dumps(report, indent=2))


def format_markdown_report(report: dict) -> str:
    d = report["dataset"]
    lines = [
        "# Churn Model: Evaluation Report",
        "",
        "Synthetic data - see data/engagement_simulator.py for the generative model "
        "and its documented independent-noise design (why this isn't a tautological "
        "inversion of the physiological signal), and docs/ML_DESIGN.md for full caveats.",
        "",
        f"Dataset: {d['num_examples']} examples across {d['num_individuals_per_persona']} synthetic "
        f"individuals/persona, {d['simulation_days']}-day simulations. Positive (30-day churn) "
        f"rate: {d['positive_rate']}.",
        "",
        "**Target AUC was deliberately bounded, not maximized (~0.70-0.85 expected):** the "
        "engagement simulator's idiosyncratic disengagement shock is designed to be comparable "
        "in magnitude to the physiology-linked engagement terms, specifically so a model can't "
        "just invert its own generator and score a suspicious ~0.99. A too-perfect AUC here "
        "would be a red flag, not a win - see data/engagement_simulator.py.",
        "",
        f"Temporal holdout: train on cutoff_day < {d['temporal_split_cutoff_day']} "
        f"({d['num_train']} examples), test on the rest ({d['num_test']} examples).",
        "",
        "## Temporal Holdout",
        "",
        "| Model | ROC-AUC | PR-AUC | Precision@top20% | Recall@top20% | F1@top20% | Brier |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, key in [
        ("Logistic Regression (shipped)", "logistic_regression"),
        ("HistGradientBoosting (benchmark only)", "hist_gradient_boosting"),
        ("Existing RewardOptimizer heuristic", "existing_reward_optimizer_heuristic"),
    ]:
        m = report["temporal_holdout"][key]
        if "error" in m:
            lines.append(f"| {label} | {m['error']} | | | | | |")
            continue
        lines.append(
            f"| {label} | {m['roc_auc']} | {m['pr_auc']} | "
            f"{m.get('precision_at_top_20pct')} | {m.get('recall_at_top_20pct')} | "
            f"{m.get('f1_at_top_20pct')} | {m.get('brier_score', '-')} |"
        )
    lines.append("")
    lines.append(
        "The logistic regression's lift (if any) over the existing heuristic is the real "
        "product-relevant number here: it's a quantified comparison against the code "
        "actually running in production today, not against a strawman."
    )
    lines.append("")
    lines.append("## Leave-One-Persona-Out Generalization (no persona one-hot)")
    lines.append("")
    lines.append(
        "Only 4 folds - a methodology demonstration given just 4 archetypes, not a "
        "statistically powered generalization claim."
    )
    lines.append("")
    lines.append("| Held-out persona | ROC-AUC | PR-AUC |")
    lines.append("|---|---|---|")
    for persona_id, m in report["leave_one_persona_out"].items():
        if "error" in m:
            lines.append(f"| {persona_id} | {m['error']} | |")
        else:
            lines.append(f"| {persona_id} | {m['roc_auc']} | {m['pr_auc']} |")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()
