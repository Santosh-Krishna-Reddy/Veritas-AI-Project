"""Train the 24h-ahead model on data/processed/train.csv and save it to ml/artifacts/.

Run: python -m ml.train
"""

from __future__ import annotations

import joblib
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor

from ml import config as C
from ml.features import TARGET_COL, build_features, feature_columns, restrict_to_period

MODEL_PATH = C.ARTIFACTS_DIR / "model.joblib"


def train_model(train_df: pd.DataFrame) -> HistGradientBoostingRegressor:
    """Fit gradient boosting on lag + calendar features. Targets stay before SPLIT_DATE."""
    feat = restrict_to_period(build_features(train_df), end=C.SPLIT_DATE)
    cols = feature_columns(feat)
    model = HistGradientBoostingRegressor(**C.MODEL_PARAMS)
    model.fit(feat[cols], feat[TARGET_COL])
    print(f"trained on {len(feat)} rows, {len(cols)} features")
    return model


def main() -> None:
    train_df = pd.read_csv(C.PROCESSED_DIR / "train.csv", parse_dates=[C.TS_COL])
    model = train_model(train_df)
    C.ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    print(f"saved {MODEL_PATH}")


if __name__ == "__main__":
    main()
