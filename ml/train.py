"""Train the 24h-ahead model on data/processed/train.csv and save it to ml/artifacts/.

Run: python -m ml.train
"""

from __future__ import annotations

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from ml import config as C
from ml.features import (TARGET_COL, build_features, feature_columns, lag_only_columns,
                         restrict_to_period)

MODEL_PATH = C.ARTIFACTS_DIR / "model.joblib"
LAGS_ONLY_PATH = C.ARTIFACTS_DIR / "model_lags_only.joblib"


def train_model(train_df: pd.DataFrame, lags_only: bool = False) -> HistGradientBoostingRegressor:
    """Fit gradient boosting. Targets stay before SPLIT_DATE. lags_only=True leaves out
    fuel mix + weather, so we can report honestly how much those extras help."""
    feat = restrict_to_period(build_features(train_df), end=C.SPLIT_DATE)
    cols = lag_only_columns(feat) if lags_only else feature_columns(feat)
    model = HistGradientBoostingRegressor(**C.MODEL_PARAMS)
    model.fit(feat[cols], feat[TARGET_COL])
    print(f"trained on {len(feat)} rows, {len(cols)} features")
    return model


def main() -> None:
    train_df = pd.read_csv(C.PROCESSED_DIR / "train.csv", parse_dates=[C.TS_COL])
    model = train_model(train_df)
    C.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(train_model(train_df, lags_only=True), LAGS_ONLY_PATH)
    print(f"saved {MODEL_PATH} and {LAGS_ONLY_PATH}")


if __name__ == "__main__":
    main()
