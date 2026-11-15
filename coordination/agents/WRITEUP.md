# WRITEUP agent — GridGreen

Read coordination/contracts.md FIRST. Owned: README.md, CREDITS.md.

BEHAVIOR: Never ask the human. Never invent a number — every figure must come from
results/metrics.json or another results/ file. If one isn't there yet, write
[PENDING: source] and come back to it.

TASK
1. Rewrite README.md using the hackathon template exactly:
   # Project name / **Track:** / **Team:** / # The problem / # What we built /
   # What we added / # How it works / # Results / # What we'd do next / # Sources
   Leave team names as [placeholders].
2. Results is the most important section. It must:
   - show persistence, last_week, model, model_lags_only, plus any variants RANKING
     adds — on BOTH MAE and cleanest_3_overlap;
   - state plainly that the model beats persistence on MAE but not on
     cleanest_3_overlap, and that overlap matches the user's decision. Lead with it.
   - report the ablation: weather + fuel mix earn -1.41 MAE and +0.025 overlap;
   - note the narrow observed range (228-488, mean 359 gCO2/kWh) as a limitation of
     the emission-factor approximation and why persistence is strong;
   - link results/failures.md.
3. "What we added": the ablation design, the leakage discipline in
   restrict_to_period(), and output framed as a decision (ml/recommend.py). Cite files.
4. CREDITS.md: EIA-930 Hourly Grid Monitor, Open-Meteo, EIA 2023 emission-factor FAQ,
   scikit-learn, pandas, numpy, joblib, FastAPI, uvicorn, Gradio, pytest, httpx,
   requests, uv — each with a link. Claude and ChatGPT Plus MUST be listed.
5. Re-read results/ periodically and replace any [PENDING].

DONE WHEN no [PENDING] remains and status.md reads "WRITEUP: done".
