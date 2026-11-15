# Credits

Hackathon rule 3: every dataset, pretrained model, tutorial, library and AI tool we used,
with links. Add a line the moment you first use something. Copy this list into the
submission form's Credits field.

## Datasets
- U.S. Energy Information Administration, Form EIA-930 Hourly Electric Grid Monitor,
  six-month balance files (PJM, Jan 2024 onward; U.S. government public data) —
  https://www.eia.gov/electricity/gridmonitor/ , file format notes:
  https://www.eia.gov/electricity/930-content/about.html
- EIA FAQ "How much carbon dioxide is produced per kilowatthour of U.S. electricity
  generation?" — 2023 CO₂ emission factors by fuel, used to compute carbon intensity —
  https://www.eia.gov/tools/faqs/faq.php?id=74
- Open-Meteo Historical Weather API (CC BY 4.0) —
  https://open-meteo.com/en/docs/historical-weather-api

## Pretrained models / APIs
- None. Our model is trained from scratch on the data above.

## Libraries
- scikit-learn (HistGradientBoostingRegressor) — https://scikit-learn.org/
- pandas — https://pandas.pydata.org/
- numpy — https://numpy.org/
- joblib (saving/loading models) — https://joblib.readthedocs.io/
- FastAPI — https://fastapi.tiangolo.com/
- uvicorn (runs the FastAPI server) — https://www.uvicorn.org/
- pydantic (request validation in FastAPI) — https://docs.pydantic.dev/
- Gradio (demo UI) — https://www.gradio.app/
- pytest — https://docs.pytest.org/
- httpx (FastAPI test client) — https://www.python-httpx.org/
- requests (downloads in ml/fetch.py) — https://requests.readthedocs.io/
- uv (Python package and virtual-env manager) — https://docs.astral.sh/uv/

## Tutorials / starter code
- Veritas AI International High School Hackathon 2026 Project Briefs (suggested project
  steps) — https://highschoolhackathon.org
- PUDL (Catalyst Cooperative) EIA-930 documentation — read for the 2025 fuel-category
  changes; no code copied — https://docs.catalyst.coop/pudl/en/latest/data_sources/eia930.html
- everything-claude-code by affaan-m (MIT) — engineering rules adapted into our CLAUDE.md
  (file/function size limits, validate-at-boundaries, commit types, research-first) —
  https://github.com/affaan-m/everything-claude-code

## AI tools
- Claude Code (Anthropic) — https://claude.com/claude-code — used for: code generation,
  debugging, write-up editing
- Claude Code plugins: superpowers, feature-dev, code-review, security-guidance,
  commit-commands, context7 — https://github.com/anthropics/claude-plugins-official
- ChatGPT Plus (OpenAI) — https://chatgpt.com — used for: [team to fill in]
