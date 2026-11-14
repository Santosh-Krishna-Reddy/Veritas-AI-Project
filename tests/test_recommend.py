import pytest

from ml.recommend import recommend


def test_recommend_basic():
    f = [500.0] * 24
    f[3], f[4], f[5], f[20] = 100.0, 120.0, 130.0, 900.0
    r = recommend(f, load_kwh=10)
    assert r["cleanest_hours_utc"] == [3, 4, 5]
    assert r["dirtiest_hour_utc"] == 20
    assert r["co2_saved_kg"] == pytest.approx((900 - 100) * 10 / 1000)


def test_recommend_rejects_bad_input():
    with pytest.raises(ValueError):
        recommend([1.0] * 23, 1)
    with pytest.raises(ValueError):
        recommend([1.0] * 24, -1)
