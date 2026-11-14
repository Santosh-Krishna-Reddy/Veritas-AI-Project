import pandas as pd
import pytest

from ml import config as C
from ml.data import clean, make_synthetic, split_by_date


@pytest.fixture(scope="session")
def series() -> pd.DataFrame:
    """~130 days of synthetic hourly data, cleaned. Small enough to keep tests fast."""
    return clean(make_synthetic(days=130))


@pytest.fixture(scope="session")
def split_date() -> str:
    return "2024-04-01"


@pytest.fixture(scope="session")
def split(series, split_date):
    return split_by_date(series, split_date)
