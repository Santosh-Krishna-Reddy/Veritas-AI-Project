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
- EIA-930 balance files, additional columns (Demand Forecast, Net Generation
  (Adjusted), Total Interchange (Adjusted)) for PJM and all columns for MISO,
  used for demand/interchange context and the MISO wind check; same public EIA
  dataset and reuse terms as above —
  https://www.eia.gov/electricity/930-content/about.html
- EIA hourly CO₂ cross-check workbook for PJM (public U.S. government data) —
  https://www.eia.gov/electricity/gridmonitor/knownissues/xls/PJM.xlsx

## Pretrained models / APIs
- None. Our model is trained from scratch on the data above.

## Libraries
- scikit-learn (HistGradientBoostingRegressor) — https://scikit-learn.org/
- pandas — https://pandas.pydata.org/
- numpy — https://numpy.org/
- joblib (saving/loading models) — https://joblib.readthedocs.io/
- FastAPI — https://fastapi.tiangolo.com/
- FastAPI/Starlette CORSMiddleware (local development CORS) —
  https://fastapi.tiangolo.com/tutorial/cors/
- uvicorn (runs the FastAPI server) — https://www.uvicorn.org/
- pydantic (request validation in FastAPI) — https://docs.pydantic.dev/
- Gradio (fallback demo UI) — https://www.gradio.app/
- openpyxl 3.1.5 (reads the EIA CO₂ cross-check workbook; one-off script only) —
  https://openpyxl.readthedocs.io/
- pytest — https://docs.pytest.org/
- httpx (FastAPI test client) — https://www.python-httpx.org/
- requests (downloads in ml/fetch.py) — https://requests.readthedocs.io/
- uv (Python package and virtual-env manager) — https://docs.astral.sh/uv/

### Web dashboard (web/)
- Next.js 16 (MIT) — https://nextjs.org/ — scaffolded with create-next-app
- React 19 (MIT) — https://react.dev/
- Tailwind CSS 4 (MIT) — https://tailwindcss.com/
- shadcn/ui components and CLI, base-nova style (MIT) — https://ui.shadcn.com/
  (card, input, button, table, chart, alert, skeleton)
- cn (MIT, class-name merging) — https://github.com/shadcn-ui/cn
- Base UI (MIT) — https://base-ui.com/
- Recharts 3 (MIT) — https://recharts.org/ — charts via shadcn chart components
- lucide-react (ISC) — https://lucide.dev/
- class-variance-authority (Apache-2.0) — https://cva.style/
- tw-animate-css (MIT) — https://github.com/Wombosvideo/tw-animate-css
- ESLint (MIT) — https://eslint.org/
- TypeScript (Apache-2.0) — https://www.typescriptlang.org/
- IBM Plex Sans, IBM Plex Sans Condensed, IBM Plex Mono (SIL Open Font License 1.1),
  loaded with next/font/google — https://github.com/IBM/plex

## Tutorials / starter code
- Veritas AI International High School Hackathon 2026 Project Briefs (suggested project
  steps) — https://highschoolhackathon.org
- PUDL (Catalyst Cooperative) EIA-930 documentation — read for the 2025 fuel-category
  changes; no code copied — https://docs.catalyst.coop/pudl/en/latest/data_sources/eia930.html
- everything-claude-code by affaan-m (MIT) — engineering rules adapted into our CLAUDE.md
  (file/function size limits, validate-at-boundaries, commit types, research-first) —
  https://github.com/affaan-m/everything-claude-code

## AI tools
- ChatGPT (OpenAI) — https://chatgpt.com/ — used November 15, 2026 for code generation and review, decision metrics audit, documentation and GitHub changes. Earlier versions did not use it.
- Claude Code (Anthropic) — https://claude.com/claude-code — used for: code generation,
  debugging, write-up editing
- Claude Code plugins: superpowers, feature-dev, code-review, security-guidance,
  commit-commands, context7 — https://github.com/anthropics/claude-plugins-official
- Claude Code `frontend-design` skill (claude-plugins-official) — design-pass guidance
  (palette, type scale, self-critique) for `web/` —
  https://github.com/anthropics/claude-plugins-official

## QA tools (not shipped with the project)
- puppeteer-core (Apache-2.0) — https://pptr.dev/ — headless Chrome screenshots and
  DOM checks at desktop and mobile widths
- Google Chrome — https://www.google.com/chrome/ — browser used for those checks
