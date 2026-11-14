"""Write the days where the model was most wrong to results/failures.md, for the write-up.

Run: python -m ml.evaluate first, then python -m ml.failures
"""

from __future__ import annotations

import pandas as pd

from ml import config as C
from ml.features import TARGET_COL, TARGET_TS_COL

N_WORST = 5


def main() -> None:
    df = pd.read_csv(C.RESULTS_DIR / "test_predictions.csv", parse_dates=[TARGET_TS_COL])
    df["abs_err"] = (df[TARGET_COL] - df["pred_model"]).abs()
    df["day"] = df[TARGET_TS_COL].dt.date
    daily = df.groupby("day").agg(
        model_mae=("abs_err", "mean"),
        persistence_mae=(TARGET_COL, lambda s: 0),  # placeholder, filled below
        true_mean=(TARGET_COL, "mean"),
    )
    daily["persistence_mae"] = (
        (df[TARGET_COL] - df["pred_persistence"]).abs().groupby(df["day"]).mean()
    )
    worst = daily.sort_values("model_mae", ascending=False).head(N_WORST)

    lines = [
        f"# Where the model fails ({C.REGION_NAME})",
        "",
        f"The {N_WORST} test days with the highest model error. For each: fill in WHY we "
        "think it failed (holiday? storm? plant outage? unusual wind?). Judges score honesty.",
        "",
        "| Day | Weekday | Model MAE | Persistence MAE | Avg true gCO2/kWh | Why (fill in) |",
        "|---|---|---|---|---|---|",
    ]
    for day, r in worst.iterrows():
        wd = pd.Timestamp(day).strftime("%a")
        lines.append(
            f"| {day} | {wd} | {r.model_mae:.0f} | {r.persistence_mae:.0f} | "
            f"{r.true_mean:.0f} | TODO |"
        )
    (C.RESULTS_DIR / "failures.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
