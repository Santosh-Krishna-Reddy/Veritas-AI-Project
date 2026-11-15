# DEMO agent — GridGreen

Read coordination/contracts.md FIRST. Owned: app.py, docs/video_script.md,
docs/hf_space_deploy.md.

BEHAVIOR: Never ask the human. Retry 5x, then log blockers and continue.

TASK
1. Run `make app`; verify the Gradio UI at http://127.0.0.1:7860 renders a forecast.
   app.py imports ml/ directly. If it errors, fix app.py.
2. Add the persistence baseline as a second line on the chart, with a caption showing
   both MAEs read from results/metrics.json at runtime. Never hardcode numbers.
3. Keep the "shift a load, save X kg CO2" interaction; check several load_kwh values.
4. Write docs/video_script.md for a 90-second screen recording:
   [0:00-0:15] problem + our user (a Chicago household with a flexible load)
   [0:15-0:50] live demo — slider, cleanest hour, kg saved
   [0:50-1:15] how it works + real numbers, INCLUDING that we beat persistence on MAE
               but not on hour-picking
   [1:15-1:30] where it fails (results/failures.md) + one next step
   Include a shot list and a pre-flight checklist.
5. Write docs/hf_space_deploy.md: deploy app.py to HuggingFace Spaces (SDK: Gradio),
   listing every file to push including ml/artifacts/model.joblib.

DONE WHEN `make app` shows both lines with live metrics and status.md reads "DEMO: done".
