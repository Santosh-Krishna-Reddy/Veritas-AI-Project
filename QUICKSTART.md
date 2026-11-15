# QUICKSTART — getting unblocked on macOS

Your `.venv` was built with Homebrew Python **3.14**, which ships a broken
`ensurepip` and a `truststore` bug that makes every `pip install` fail on
macOS 26 (Tahoe). Rebuild the environment on Python 3.12 and everything works.

## One-time setup

```bash
cd ~/Veritas-AI-Project
rm -rf .venv
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Verify:

```bash
python -c "import sklearn, pandas, fastapi, gradio; print('ok')"
```

Should print `ok`. If `python3.12` is not found, run `brew install python@3.12`
first.

## Every new terminal

```bash
cd ~/Veritas-AI-Project
source .venv/bin/activate
```

Once activated, plain `python` and `make` both use the right interpreter — no
more `python3.12` prefixes, no `--break-system-packages`.

## Running the project

```bash
make fetch      # downloads EIA-930 six-month files + Open-Meteo weather (no API key)
make data       # builds data/processed/train.csv and test.csv
make train      # fits model.joblib + model_lags_only.joblib
make eval       # writes results/metrics.json  <- the numbers for your write-up
make failures   # writes the failure-case analysis
make app        # opens the demo UI at http://127.0.0.1:7860
```

Or all the way through in one go:

```bash
make pipeline   # fetch -> data -> train -> eval -> failures
make app
```

## Notes

- **No EIA API key is needed.** `ml/config.py` points at the EIA-930 six-month
  *balance* CSV files, which are public downloads. The `.env` key you set is
  harmless but unused by this pipeline.
- `make fetch` downloads several large CSVs (2024 H1 through 2026 H2). Expect a
  few minutes and a few hundred MB in `data/raw/eia_cache/`.
- If `make fetch` fails on a URL, the six-month file for the current half-year
  may not be published yet. Lower `FETCH_START_YEAR` or drop the most recent
  half in `ml/config.py` and rerun.
- The demo UI (`make app`) imports `ml/` directly — no API server needed. Run
  `make api` separately only if you want the HTTP endpoints for the write-up.

## Deploying the demo (optional, free)

The Gradio app deploys to HuggingFace Spaces with no build step:

1. Create a Space at https://huggingface.co/new-space → SDK: **Gradio**
2. Push `app.py`, `requirements.txt`, `ml/`, and `ml/artifacts/model.joblib`
3. It builds and serves automatically; the URL goes in your submission

This avoids needing both Render and Vercel.
