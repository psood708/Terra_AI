# ML Design Notes

This document is the honest engineering record behind the three ML/NLP systems in this
repo — what's real, what's synthetic, why each technique was sized the way it was, and
the actual before/after numbers each one produced. It exists because a reviewer is more
likely to read this than to run `training/` and `evals/` themselves, and because every
claim here needs to be defensible in an interview, not just present in the code.

## The synthetic-data honesty caveat (read this first)

Every number behind the anomaly detector, the churn model, and the eval harness's
grounding checks comes from **synthetic data**, not real Terra users:

- `data/persona_archetypes.py` samples 50-100 synthetic individuals per persona from a
  distribution around that persona's baseline (not 4 fixed numbers).
- `data/longitudinal_simulator.py` runs a per-metric mean-reverting AR(1) process with
  weekday/weekend seasonality and injected life events (illness, travel, overtraining,
  alcohol) at a documented, persona-specific magnitude and 1-4 day decay — this event
  log is the anomaly detector's ground truth.
- `data/engagement_simulator.py` drives a hidden `habit_strength` random walk into a
  Bernoulli `app_opened` draw, coupled only weakly to physiology (see below for why
  that coupling is deliberately weak).

None of this is a claim about real-world model performance. It's a claim about
methodology: given a reasonably realistic generative model of the problem, do the
chosen techniques behave the way the theory predicts, fail gracefully where expected,
and honestly report where they don't win.

## 1. Anomaly Detection — per-persona MAD control chart

**Problem with the original code:** `detect_anomalies` used one fixed threshold for
every persona (e.g. HRV drop ≥ 15ms). That's statistically indefensible the moment two
personas have different day-to-day variability — which they do (Marcus's resting HRV
is naturally low-variance; Sarah's is naturally high-variance as a trained athlete).

**What replaced it:** a per-persona, per-metric rolling **median + MAD (modified
z-score) control chart** (`models/anomaly_detector.py`, baselines trained by
`training/train_anomaly_baselines.py`): `modified_z = 0.6745·(x_t − median(window)) /
MAD(window)`, flagged at `|modified_z| > 3.5` (Iglewicz & Hoaglin's standard cutoff),
over a trailing 14-21 day window that excludes the current point (no lookahead — see
`test_anomaly_detector.py::test_rolling_mad_flags_no_lookahead_...`). An `IsolationForest`
runs as a **secondary** layer over rolling engineered features (mean/std/rate-of-change)
to catch correlated multi-metric drift a single-metric z-score misses.

**Why IsolationForest is secondary, not primary:** the per-persona time series here is
low-dimensional and small-N. Positioning a general-purpose multivariate anomaly detector
as the primary tool over that would read as reaching for a bigger hammer than the
problem needs — decorative ML. A calibrated univariate control chart is the right-sized
primary tool; IsolationForest earns its place only as a secondary net for what the
univariate check structurally can't see.

**Results — reported in full, not cherry-picked** (`training/reports/anomaly_detection_report.md`,
regenerate with `python training/train_anomaly_baselines.py`):

### alex_longevity (6 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | FP / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 0.50 | 1.00 | 0.143 | 0.250 | 0.00 |
| MAD control chart | 0.833 | 0.682 | 0.429 | 0.526 | 0.93 |
| MAD + IsolationForest | 0.833 | 0.633 | 0.543 | 0.585 | 1.46 |

### sarah_athlete (3 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | FP / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 1.00 | 1.00 | 0.391 | 0.562 | 0.00 |
| MAD control chart | 1.00 | 0.571 | 0.522 | 0.545 | 1.19 |
| MAD + IsolationForest | 1.00 | 0.533 | 0.696 | 0.604 | 1.86 |

### marcus_metabolic (13 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | FP / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 0.538 | 1.00 | 0.221 | 0.362 | 0.00 |
| MAD control chart | 0.615 | 0.947 | 0.234 | 0.375 | 0.13 |
| MAD + IsolationForest | 0.692 | 0.741 | 0.260 | 0.385 | 0.93 |

### elena_cognitive (8 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | FP / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 0.875 | 1.00 | 0.347 | 0.515 | 0.00 |
| MAD control chart | 0.625 | 0.556 | 0.238 | 0.333 | 1.06 |
| MAD + IsolationForest | 0.750 | 0.560 | 0.333 | 0.418 | 1.46 |

**Read this honestly, not optimistically:** MAD does not uniformly dominate the legacy
threshold. It improves event recall and F1 substantially for `alex_longevity` and
`marcus_metabolic`, but trades away day-level precision for `sarah_athlete` and
`elena_cognitive` without a clear net win there — and each persona has only 3-13
injected events, too few to expect a clean, uniform winner. A window-width sweep
(14/21/28 days) shows the same pattern: wider windows cut false positives but cost
recall, with no single window dominating across personas.

The actual argument for MAD was never "it detects strictly more events" — it's that a
flat 15ms/5bpm margin applied identically regardless of a persona's own baseline
variability is the indefensible part, and MAD fixes that specific, statistically real
flaw regardless of whether the aggregate detection numbers move up or down for any one
persona.

## 2. Churn/Retention Classifier

**Why this had to be built from scratch:** the original `mock_generator.py` had no
concept of app engagement or sessions at all — there was no data to train a churn model
on. `data/engagement_simulator.py` and `data/persona_archetypes.py` (Phase 3) exist
specifically to create that data before any model could be fit.

**The critical design constraint — stated explicitly because it's the first question
a reviewer should ask:** if engagement were driven only by a boost term tied to
physiology (workout completion, recovery, streaks), a churn classifier would just be
inverting the generator's own formula, and would score a suspicious ~0.99 AUC. That's
not a win, it's a tell that the "model" learned the label-generating function instead
of a genuine physiology-engagement relationship. `engagement_simulator.py`'s
`habit_strength` random walk includes an **independent noise/friction term not derived
from physiology**, deliberately sized so physiological signals are *correlated with*,
not *determinative of*, churn. The target AUC band (0.70-0.85) was chosen on purpose,
not hit by accident — see `training/reports/churn_model_report.md`.

**Model:** logistic regression as the shipped model (interpretable — "streak breaks
raise churn odds by X%" is a real growth-marketing talking point, matching the job
posting's retention angle) with `HistGradientBoostingClassifier` benchmarked but not
shipped. Features are strictly backward-looking from the label cutoff: trailing
engagement counts/trends, streak length and break count, recovery-score trend/volatility,
Phase 2's anomaly-flag count, and OdinAI query count.

**Results** (`training/train_churn_model.py`; dataset: 4,160 examples across 40
synthetic individuals × 4 personas, 240-day simulations, 18.8% 30-day-churn positive rate):

### Temporal holdout (train on day < 156, test on the rest)

| Model | ROC-AUC | PR-AUC | Precision@top20% | Recall@top20% | F1@top20% | Brier |
|---|---|---|---|---|---|---|
| **Logistic Regression (shipped)** | **0.834** | **0.461** | 0.469 | 0.440 | 0.454 | 0.1295 |
| HistGradientBoosting (benchmark only) | 0.830 | 0.469 | 0.453 | 0.425 | 0.439 | 0.1488 |
| Existing `RewardOptimizer` heuristic (`completion_ratio`) | 0.514 | 0.218 | 0.266 | 0.249 | 0.257 | — |

The gap between the shipped model (0.834 AUC) and the heuristic already running in
production (0.514 AUC, barely above chance) is the real product-relevant number here —
a quantified lift over the actual code being replaced, not a strawman comparison.

### Leave-one-persona-out generalization (4 folds — a methodology demo, not a powered claim)

| Held-out persona | ROC-AUC | PR-AUC |
|---|---|---|
| alex_longevity | 0.831 | 0.430 |
| sarah_athlete | 0.814 | 0.392 |
| marcus_metabolic | 0.810 | 0.453 |
| elena_cognitive | 0.825 | 0.422 |

Stable AUC across held-out personas (0.81-0.83) suggests the model is picking up a
genuine cross-persona engagement pattern rather than overfitting to one archetype's
idiosyncrasies — though again, 4 folds is a demonstration of the *evaluation
methodology* (temporal holdout + leave-one-group-out), not a statistically powered
generalization claim.

## 3. LLM Eval Harness + Prompt Versioning

This is the direct answer to the job posting's "testing AI models" / "fine-tuning AI
performance metrics" language. `prompts/odin_prompts.py` holds a versioned registry
(`PROMPTS = {"v1": ..., "v2": ...}`) instead of one inline f-string; `evals/run_eval.py`
runs ~32 golden queries (`evals/golden_queries.json`, spanning direct-metric,
recommendation, citation-seeking, out-of-scope, and missing-data categories, replicated
across all 4 personas) against whichever `PROMPT_VERSION` is active.

**Deterministic checks are the backbone, not an LLM judge** — the single most important
one for a wearable-data assistant is **numeric grounding**: does the response reference
at least one real number from the persona's actual telemetry, within tolerance? Also
checked: **citation validity** against `data/citations_corpus.json` (this is a real
regression guard — a fabricated citation was found in this project's original code
before Phase 4), and **scope handling** (does an out-of-scope/missing-data query avoid
fabricating a specific number it has no source for?). A small ~8-query LLM-as-judge
tier exists (`--llm-judge`) but is explicitly secondary/directional, gated behind a live
API key, and never part of the pass/fail harness.

**Before/after prompt comparison** (`evals/compare_reports.py --latest v1 v2`):

| Metric | v1 | v2 | Delta |
|---|---|---|---|
| numeric_grounding_rate | 1.0 | 1.0 | 0.0 |
| citation_validity_rate | 1.0 | 1.0 | 0.0 |
| scope_handling_rate | 1.0 | 1.0 | 0.0 |
| mean_latency_ms | 11.5 | 16.3 | +4.8 |

**Honest caveat, surfaced automatically by the tool itself:** neither run here had a
live LLM API key configured, so both executed entirely against the deterministic
fallback engine, which doesn't read the system prompt at all — this specific diff
can't show a genuine prompt-version effect on response quality. What it does prove is
the mechanism: change `PROMPT_VERSION`, rerun, get a real structural diff between two
timestamped reports. Rerunning with `--api-key <a Hugging Face token>` on both versions
would surface actual prompt-driven differences in grounding/citation behavior.

## 4. Citation Retrieval

`SCIENTIFIC_CITATIONS` (5 hardcoded entries, naive keyword-substring matching) became a
60-entry corpus (`data/citations_corpus.json`) retrieved via **TF-IDF + cosine
similarity** (`models/citation_retriever.py`) as the primary path. For ~60 short,
keyword-dense entries, sparse lexical retrieval is deterministic, zero-latency, has no
external failure mode during a live demo, and is exactly unit-testable (known query →
known ranking, see `test_citation_retriever.py`). A Hugging Face hosted-embeddings tier
exists as an **optional secondary upgrade**, not the primary path — the same
right-sized-tool judgment call as IsolationForest in section 1: know when *not* to
reach for the heavier model.

## Why these specific techniques, not bigger ones

Every choice above sizes the tool to the actual data: 4 personas × a few hundred days
is not enough signal for the heaviest tool that could nominally be applied to each
problem, and reaching for one anyway would be decorative, not more rigorous. A
per-persona MAD chart, a logistic regression with an explicit AUC ceiling, TF-IDF over a
60-entry corpus, and a deterministic-first eval harness are each the right-sized answer
to their respective problem — with the heavier alternative (IsolationForest,
gradient boosting, embeddings, LLM-as-judge) kept as an explicitly secondary,
benchmarked-but-not-load-bearing layer. That contrast — and being able to explain *why*
the bigger tool was deliberately not made the primary one — is the actual interview
answer this document is written to support.

## Regenerating these numbers

```bash
python training/train_anomaly_baselines.py   # -> training/reports/anomaly_detection_report.{json,md}
python training/train_churn_model.py         # -> training/reports/churn_model_report.{json,md}
python -m evals.run_eval                     # -> evals/reports/<PROMPT_VERSION>_<timestamp>.json
python -m evals.compare_reports --latest v1 v2
pytest tests/ -v                             # full suite, including ML unit tests
```
