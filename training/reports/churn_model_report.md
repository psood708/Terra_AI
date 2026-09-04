# Churn Model: Evaluation Report

Synthetic data - see data/engagement_simulator.py for the generative model and its documented independent-noise design (why this isn't a tautological inversion of the physiological signal), and docs/ML_DESIGN.md for full caveats.

Dataset: 4160 examples across 40 synthetic individuals/persona, 240-day simulations. Positive (30-day churn) rate: 0.188.

**Target AUC was deliberately bounded, not maximized (~0.70-0.85 expected):** the engagement simulator's idiosyncratic disengagement shock is designed to be comparable in magnitude to the physiology-linked engagement terms, specifically so a model can't just invert its own generator and score a suspicious ~0.99. A too-perfect AUC here would be a red flag, not a win - see data/engagement_simulator.py.

Temporal holdout: train on cutoff_day < 156 (2880 examples), test on the rest (1280 examples).

## Temporal Holdout

| Model | ROC-AUC | PR-AUC | Precision@top20% | Recall@top20% | F1@top20% | Brier |
|---|---|---|---|---|---|---|
| Logistic Regression (shipped) | 0.834 | 0.461 | 0.469 | 0.44 | 0.454 | 0.1295 |
| HistGradientBoosting (benchmark only) | 0.83 | 0.469 | 0.453 | 0.425 | 0.439 | 0.1488 |
| Existing RewardOptimizer heuristic | 0.514 | 0.218 | 0.266 | 0.249 | 0.257 | - |

The logistic regression's lift (if any) over the existing heuristic is the real product-relevant number here: it's a quantified comparison against the code actually running in production today, not against a strawman.

## Leave-One-Persona-Out Generalization (no persona one-hot)

Only 4 folds - a methodology demonstration given just 4 archetypes, not a statistically powered generalization claim.

| Held-out persona | ROC-AUC | PR-AUC |
|---|---|---|
| alex_longevity | 0.831 | 0.43 |
| sarah_athlete | 0.814 | 0.392 |
| marcus_metabolic | 0.81 | 0.453 |
| elena_cognitive | 0.825 | 0.422 |
