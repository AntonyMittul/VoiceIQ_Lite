from datetime import date

from app.data.generate import generate_tasks
from app.ml.baseline import baseline_predictions, baseline_score
from app.ml.features import FEATURE_COLUMNS, add_delay_label, build_features
from app.ml.train import explain_prediction, train_risk_model


def test_features_and_baseline_are_bounded() -> None:
    frame = generate_tasks(80, seed=42, as_of=date(2026, 1, 1))
    features = build_features(frame, as_of=date(2026, 1, 1))
    scores = baseline_score(frame, as_of=date(2026, 1, 1))
    assert set(FEATURE_COLUMNS).issubset(features.columns)
    assert scores.between(0, 1).all()
    assert len(baseline_predictions(frame)) == 80


def test_model_uses_time_split_and_emits_explanations() -> None:
    frame = generate_tasks(160, seed=42, as_of=date(2026, 1, 1))
    model, metrics = train_risk_model(frame, as_of=date(2026, 1, 1))
    assert metrics["train_records"] + metrics["test_records"] == 160
    assert metrics["model"]["recall"] >= 0
    row = add_delay_label(frame, as_of=date(2026, 1, 1)).iloc[0]
    explanations = explain_prediction(model, row)
    assert explanations
    assert explanations[0]["feature"] in FEATURE_COLUMNS

