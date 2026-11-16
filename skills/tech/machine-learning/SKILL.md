---
name: machine-learning
description: Machine learning engineering in Python - problem framing, data splits and leakage prevention, baselines, evaluation and metrics, reproducibility, experiment tracking, training pipelines, and model serving checks. Use only when the project trains, evaluates, or serves ML models (scikit-learn, PyTorch, TensorFlow, XGBoost, LightGBM, and similar) and the task touches data preparation, training, evaluation, or inference code.
---

# Machine Learning

Tier 3. Activate only if the project uses ML libraries. Combine with
`python-data-engineering` for data preparation and `python-testing` for tests.

## Frame the problem first

- State the decision the model supports, the target, the unit of prediction, and
  the metric that reflects the real cost of errors. Accuracy on imbalanced data
  is rarely that metric.
- Establish a baseline before any model work: a constant or majority predictor, a
  simple heuristic, and a simple model (linear or small tree). A complex model
  must beat these to justify itself. This is "subtract before you add" for ML.

## Data splits and leakage

Leakage is the most common cause of results that do not hold in production.

- Split before any fitting. Fit scalers, encoders, imputers, feature selection,
  and vocabulary on the training split only; use a `Pipeline` so this is
  structural rather than a matter of care.
- Split by the unit that must generalize: by group (user, patient, device) when
  rows of one entity correlate; by time when predicting the future. Random splits
  on such data overestimate quality.
- The test set is used once, for the final estimate. Tune on validation data or
  with cross-validation.
- Check features for information unavailable at prediction time, including
  proxies of the target and post-event fields. Remove duplicates across splits.
- A result that looks too good is a leak until shown otherwise: attack the premise.

## Evaluation

- Report metrics appropriate to the task: precision/recall/F1, PR-AUC, ROC-AUC,
  calibration for classification; MAE/RMSE and error distribution for regression;
  ranking metrics for ranking.
- Report uncertainty: cross-validation spread, confidence intervals, or several
  seeds. A difference smaller than the noise is not an improvement.
- Evaluate on meaningful slices (segments, classes, time periods), not only the
  aggregate. Inspect actual errors.
- Choose decision thresholds on validation data according to error costs.
- Compare against the baseline and the current production model on the same data.

## Reproducibility

- Fix and record seeds (`random`, NumPy, framework, data loader workers); note
  where determinism is not guaranteed (GPU operations).
- Record for every run: code version, data version or hash, configuration,
  environment (lock file), metrics, and the produced artifact. Use the project's
  tracker (MLflow, Weights & Biases, DVC) or a structured run directory.
- Configuration lives in files or typed config objects, not in edited constants.
- A training run is launched by one command from a clean checkout.
- Keep exploratory notebooks out of the production path; move code that matters
  into tested modules.

## Training code

- Separate data loading, feature building, model definition, training loop, and
  evaluation into testable units.
- Validate input data schema and ranges before training and before inference
  (the same code for both, to prevent training/serving skew).
- Checkpoint long runs; make them resumable. Use early stopping on validation data.
- Watch training and validation curves; diagnose overfitting or underfitting
  before changing the architecture.
- Do not start expensive training or tuning jobs without the user's agreement.

## Testing ML code

Test behavior that should hold regardless of the learned weights:

- data transformations on small hand-built inputs;
- output shapes, dtypes, value ranges, probability sums;
- the model can overfit a tiny batch (the training loop works);
- determinism with a fixed seed where expected;
- invariances and directional expectations for the domain;
- save → load → predict gives identical results;
- a quality floor on a small fixed dataset as a regression guard, with tolerance.

Do not assert exact metric values that depend on nondeterministic training.

## Serving and artifacts

- Version model artifacts together with the preprocessing they need; ship them as
  one unit.
- Do not load untrusted pickle or `torch.load` files; prefer safe formats
  (`safetensors`, ONNX) for artifacts from outside.
- Measure inference latency and memory on realistic inputs; batch where it helps.
- Monitor in production: input drift, prediction distribution, and outcome
  metrics when labels arrive. Define a rollback to the previous model.

## Data and ethics

Handle personal and sensitive data per the project's rules; do not copy datasets
to external services; check per-group performance where decisions affect people.

## Report

The baseline, the split method and why it is leak-free, metrics with uncertainty
and slices, the comparison to baseline, how to reproduce the run, and known limits.
