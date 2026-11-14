import numpy as np

from ml import config as C
from ml.baseline import BASELINES
from ml.evaluate import cleanest_k_overlap, evaluate
from ml.features import TARGET_COL, build_features, feature_columns, restrict_to_period
from ml.train import train_model


def test_baselines_run(series, split_date):
    feat = restrict_to_period(build_features(series), start=split_date)
    for name, fn in BASELINES.items():
        p = fn(feat)
        assert len(p) == len(feat) and np.isfinite(p).all(), name


def test_model_beats_or_ties_persistence_on_synthetic(split, split_date, monkeypatch):
    """On synthetic data with a strong daily pattern the model should not be worse than
    persistence. (Real data is the real test; this guards against a broken pipeline.)"""
    monkeypatch.setattr(C, "SPLIT_DATE", split_date)
    train, test = split
    model = train_model(train)
    import pandas as pd
    feat = restrict_to_period(build_features(pd.concat([train, test])), start=split_date)
    preds = {n: f(feat) for n, f in BASELINES.items()}
    preds["model"] = pd.Series(model.predict(feat[feature_columns(feat)]))
    m = evaluate(feat, preds)
    assert m["model"]["mae"] <= m["persistence"]["mae"] * 1.05
    for v in m.values():
        assert 0 <= v[f"cleanest_{C.CLEANEST_K}_overlap"] <= 1


def test_cleanest_overlap_perfect_prediction(series, split_date):
    feat = restrict_to_period(build_features(series), start=split_date)
    assert cleanest_k_overlap(feat, feat[TARGET_COL]) == 1.0
