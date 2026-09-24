import argparse
import json
import pickle
from datetime import UTC, date, datetime
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.baseline import baseline_predictions
from app.ml.features import FEATURE_COLUMNS, add_delay_label


def time_split(data: pd.DataFrame, train_fraction: float = 0.8) -> tuple[pd.DataFrame, pd.DataFrame]:
    ordered = data.sort_values("created_date").reset_index(drop=True)
    cutoff = max(1, min(len(ordered) - 1, int(len(ordered) * train_fraction)))
    return ordered.iloc[:cutoff].copy(), ordered.iloc[cutoff:].copy()


def classification_metrics(actual: pd.Series, predicted: pd.Series, scores: pd.Series | None = None) -> dict[str, float]:
    metrics = {
        "precision": round(precision_score(actual, predicted, zero_division=0), 4),
        "recall": round(recall_score(actual, predicted, zero_division=0), 4),
        "f1": round(f1_score(actual, predicted, zero_division=0), 4),
    }
    if scores is not None and actual.nunique() > 1:
        metrics["roc_auc"] = round(roc_auc_score(actual, scores), 4)
    return metrics


def train_risk_model(frame: pd.DataFrame, as_of: date | None = None) -> tuple[Pipeline, dict[str, object]]:
    labeled = add_delay_label(frame, as_of)
    train, test = time_split(labeled)
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
        ]
    )
    model.fit(train[FEATURE_COLUMNS], train["delayed_label"])
    probabilities = model.predict_proba(test[FEATURE_COLUMNS])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    baseline = baseline_predictions(test, as_of=as_of)
    metrics = {
        "model_version": "logistic-regression-v1",
        "trained_at": datetime.now(UTC).isoformat(),
        "train_records": len(train),
        "test_records": len(test),
        "positive_rate": round(float(labeled["delayed_label"].mean()), 4),
        "features": FEATURE_COLUMNS,
        "baseline": classification_metrics(test["delayed_label"], baseline),
        "model": classification_metrics(test["delayed_label"], predictions, pd.Series(probabilities)),
    }
    return model, metrics


def explain_prediction(model: Pipeline, row: pd.Series) -> list[dict[str, float | str]]:
    classifier = model.named_steps["classifier"]
    scaler = model.named_steps["scaler"]
    values = row[FEATURE_COLUMNS].astype(float).to_numpy()
    scaled_values = scaler.transform(pd.DataFrame([values], columns=FEATURE_COLUMNS))[0]
    contributions = classifier.coef_[0] * scaled_values
    explanations = [
        {"feature": feature, "contribution": round(float(contribution), 4)}
        for feature, contribution in zip(FEATURE_COLUMNS, contributions, strict=True)
    ]
    return sorted(explanations, key=lambda item: abs(float(item["contribution"])), reverse=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Train and evaluate the VoiceIQ delay-risk model")
    parser.add_argument("input", type=Path)
    parser.add_argument("--model-output", type=Path, default=Path("models/risk_model.pkl"))
    parser.add_argument("--metrics-output", type=Path, default=Path("models/risk_metrics.json"))
    args = parser.parse_args()
    frame = pd.read_csv(args.input)
    model, metrics = train_risk_model(frame)
    args.model_output.parent.mkdir(parents=True, exist_ok=True)
    with args.model_output.open("wb") as output:
        pickle.dump(model, output)
    args.metrics_output.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
