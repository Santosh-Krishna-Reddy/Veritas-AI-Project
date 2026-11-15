# Blockers

Agents append here when stuck after 5 honest attempts. QA reads this file and
relays to the human. Never delete another agent's entry; add a resolution line
underneath it instead.

Format:
    ## [AGENT] 2026-11-14T19:05Z
    What I was doing:
    What blocked me (exact error / what I could not reach):
    What I need from the human:
    What I did instead while waiting:

---

## [DEMO] 2026-11-15T04:45Z
What I was doing: verifying `make app` forecasts.
What blocked me: two issues in files DEMO does not own. Not blocking the demo.
  1. ml/data.py (shared): the last 3 rows of data/processed/test.csv (2026-11-14 06:00–08:00 UTC)
     are exact copies of 05:00 (CI 373.89, demand 90893). Looks like trailing-gap filling at the end
     of the series. That makes the tail of the app's persistence line flat (Sun 12–2 AM).
     Proposal: drop trailing gap hours instead of filling them.
  2. requirements.txt (unowned): says `gradio>=4.0`, but app.py needs Gradio 6 (`launch(theme=)`;
     `overlay_point` was removed in 6). Proposal: change it to `gradio>=6.0`.
What I need from the human: approve or reject both proposals.
What I did instead: app.py works with the installed Gradio 6.32.0; hf_space_deploy.md pins sdk_version 6.32.0.
