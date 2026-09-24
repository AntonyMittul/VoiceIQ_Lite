import pandas as pd

from app.ml.features import add_delay_label


def baseline_score(frame: pd.DataFrame, as_of=None) -> pd.Series:
    data = add_delay_label(frame, as_of)
    score = (
        data["days_until_due"].lt(0).astype(float) * 0.40
        + data["previous_delay_count"].clip(upper=3).div(3) * 0.25
        + (100 - data["progress_pct"].clip(lower=0, upper=100)).div(100) * 0.20
        + data["has_blocker"] * 0.10
        + data["priority_score"].div(3) * 0.05
    )
    return score.clip(0, 1)


def baseline_predictions(frame: pd.DataFrame, threshold: float = 0.5, as_of=None) -> pd.Series:
    return (baseline_score(frame, as_of) >= threshold).astype(int)

