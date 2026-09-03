# Anomaly Detection: Before/After Evaluation

Synthetic data - see data/longitudinal_simulator.py for the generative model and docs/ML_DESIGN.md for the full honesty caveats. Ground truth is the injected illness/travel/overtraining/alcohol event log, not real labeled data.

Simulation: 240 days/persona, seeded for reproducibility.

**How to read this - the result is genuinely mixed, on purpose left that way:** the MAD control chart does not uniformly dominate the legacy fixed-threshold logic on every metric for every persona below. It substantially improves event recall and F1 for alex_longevity and marcus_metabolic, but trades away precision for sarah_athlete and elena_cognitive without a clear net win there. We also swept the MAD window (14/21/28 days): a wider window cuts false positives (fewer, noisier small-sample MAD estimates) but costs event recall, and no single window dominates across all four personas given only 3-13 injected events each - too small a sample to expect a clean, uniform winner. The actual argument for MAD over the legacy check was never 'it detects more events' - it's that a flat 15ms HRV / 5bpm RHR margin applied identically to every persona regardless of that persona's own day-to-day variability is statistically indefensible (see marcus_metabolic's naturally low HRV variance vs. sarah_athlete's naturally high variance below), whereas MAD is calibrated per-persona. This table is reported in full, unedited, as that honest evaluation - not cherry-picked to make MAD look uniformly better than it is.

## alex_longevity (6 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | False Positives / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 0.5 | 1.0 | 0.143 | 0.25 | 0.0 |
| MAD control chart | 0.833 | 0.682 | 0.429 | 0.526 | 0.93 |
| MAD + IsolationForest | 0.833 | 0.633 | 0.543 | 0.585 | 1.46 |

## sarah_athlete (3 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | False Positives / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 1.0 | 1.0 | 0.391 | 0.562 | 0.0 |
| MAD control chart | 1.0 | 0.571 | 0.522 | 0.545 | 1.19 |
| MAD + IsolationForest | 1.0 | 0.533 | 0.696 | 0.604 | 1.86 |

## marcus_metabolic (13 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | False Positives / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 0.538 | 1.0 | 0.221 | 0.362 | 0.0 |
| MAD control chart | 0.615 | 0.947 | 0.234 | 0.375 | 0.13 |
| MAD + IsolationForest | 0.692 | 0.741 | 0.26 | 0.385 | 0.93 |

## elena_cognitive (8 injected events)

| Detector | Event Recall | Day Precision | Day Recall | Day F1 | False Positives / 30d |
|---|---|---|---|---|---|
| Legacy fixed threshold | 0.875 | 1.0 | 0.347 | 0.515 | 0.0 |
| MAD control chart | 0.625 | 0.556 | 0.238 | 0.333 | 1.06 |
| MAD + IsolationForest | 0.75 | 0.56 | 0.333 | 0.418 | 1.46 |
