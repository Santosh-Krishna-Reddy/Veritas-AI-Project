# GridGreen — next-day grid carbon intensity forecast

**Track:** Climate
**Team:** Name 1, Name 2, Name 3

# The problem

Who has this problem, and why does it matter? (2-3 sentences)

# What we built

What goes in, what comes out, and how someone would use it.

# What we added

If you started from a suggested project: which one, and what you added
or changed (your own user, data or question). Otherwise, write "Our own idea".

Our own idea.

# How it works

Data: which dataset, how many examples, how we cleaned it.
Model: what we used and why.

# Results

Our baseline scored X. Our model scored Y on held-out test data.
Where it fails, and why we think so.

<!-- Copy numbers from results/metrics.json and examples from results/failures.md. Never invent. -->

# What we'd do next

One or two concrete next steps with more time.

# Sources

Datasets, pretrained models, tutorials and AI tools used, with links.
(Keep in sync with CREDITS.md.)

---

## Run it yourself

```bash
pip install -r requirements.txt
make fetch    # (optional, needs internet) re-download EIA-930 + Open-Meteo → data/raw/
make data     # clean + split by date (train < 2026-08-01 <= test)
make train    # train model → ml/artifacts/
make eval     # baseline vs model on the test set → results/metrics.json
make demo     # Gradio demo
make api      # FastAPI on http://localhost:8000
```
