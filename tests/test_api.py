import pytest

fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from ml.train import MODEL_PATH  # noqa: E402


@pytest.mark.skipif(not MODEL_PATH.exists(), reason="run `make train` first")
def test_predict_endpoint():
    from api.main import app
    c = TestClient(app)
    r = c.post("/predict", json={"history": [400.0] * 168, "load_kwh": 7})
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body["forecast_gco2_per_kwh"]) == 24
    assert len(body["cleanest_hours_utc"]) == 3


def test_predict_rejects_short_history():
    from api.main import app
    c = TestClient(app)
    assert c.post("/predict", json={"history": [400.0] * 10}).status_code == 422
