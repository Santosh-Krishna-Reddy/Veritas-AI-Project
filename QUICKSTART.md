# QUICKSTART — getting unblocked on macOS

Homebrew's `pip` is broken on macOS 26 (its vendored `truststore` crashes because
`platform.mac_ver()` returns an empty string). Use `uv` instead; it is a standalone
binary with no such dependency. The project venv lives at `.venv`.

## One-time setup

```bash
cd ~/Veritas-AI-Project
uv venv --python 3.12
uv pip install -r requirements.txt
```

Verify:

```bash
.venv/bin/python -c "import sklearn, pandas, fastapi, gradio; print('ok')"
```

Should print `ok`. If `uv` is not found, run `brew install uv` first. Never use
`pip install`, `python3 -m venv` or `--break-system-packages` on this machine.

## Every new terminal

`make` calls `.venv/bin/python` directly, so nothing needs to be activated:

```bash
cd ~/Veritas-AI-Project
make test
```

## Running the project

```bash
make fetch      # downloads EIA-930 six-month files + Open-Meteo weather (no API key)
make data       # builds data/processed/train.csv and test.csv
make train      # fits model.joblib + model_lags_only.joblib
make eval       # writes results/metrics.json  <- the numbers for your write-up
make rank       # ranking-variant diagnosis
make failures   # writes the failure-case analysis
make decision   # writes the post-hoc decision audit
```

Or all the way through in one go:

```bash
make pipeline
```

Demo (custom Next.js dashboard, the recorded entry point):

```bash
make api                                  # terminal 1: http://localhost:8000
cd web && npm install && npm run dev      # terminal 2: http://localhost:3000
```

Fallback (single process, no Node): `make app` serves the redesigned Gradio
dashboard at http://127.0.0.1:7860.

## Notes

- **No EIA API key is needed.** `ml/config.py` points at the EIA-930 six-month
  *balance* CSV files, which are public downloads. The `.env` key you set is
  harmless but unused by this pipeline.
- `make fetch` downloads several large CSVs (2024 H1 through 2026 H2). Expect a
  few minutes and a few hundred MB in `data/raw/eia_cache/`.
- If `make fetch` fails on a URL, the six-month file for the current half-year
  may not be published yet. Lower `FETCH_START_YEAR` or drop the most recent
  half in `ml/config.py` and rerun.
- The Gradio UI (`make app`) imports `ml/` directly — no API server needed. The
  Next.js dashboard (`web/`) needs `make api` running.

## Deploying the demo (optional, free)

The Gradio app deploys to HuggingFace Spaces with no build step:

1. Create a Space at https://huggingface.co/new-space → SDK: **Gradio**
2. Push `app.py`, `requirements.txt`, `ml/`, and `ml/artifacts/model.joblib`
3. It builds and serves automatically; the URL goes in your submission

This avoids needing both Render and Vercel.
