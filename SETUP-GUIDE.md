# Veritas AI Hackathon — Claude Code Setup Guide (start to finish)

Deadline: **Sun Nov 15, 11:59 PM ET = 10:59 PM CT**. Work the phases in order. Times are CT.

---

## Phase 0 — Decide (do this first, ~30 min, all three of you)

Nothing below is useful until these are answered. Write the answers into `CLAUDE.md` §0.

1. **Track:** Health / Finance / Climate / Languages. Pick the one your team cares about most
   (the FAQ says there is no "easier" track).
2. **Project:** suggested project from the briefs, or your own idea inside the track.
3. **The one thing you add:** your own user, your own data, or your own question. This is
   worth 20 pts (Originality) and separates you from every other team doing the same brief.
4. **Stack decision (already made in CLAUDE.md §4):** Python does the ML; Next.js is only a
   demo shell; Gradio is the fallback. Rule 3 of the briefs says an app built with AI coding
   tools "doesn't count on its own" — the model is the product.
5. **Who owns what:**
   - Person A: data + baseline + model (`ml/`)
   - Person B: API + demo UI (`api/`, `web/` or `ml/demo.py`)
   - Person C: README write-up, CREDITS.md, video, submission form
   Rotate the Claude Pro login so one person isn't rate-limited while the others wait.

---

## Phase 1 — Install Claude Code on each laptop (~10 min each)

```bash
# macOS / Linux
curl -fsSL https://claude.ai/install.sh | bash
# Windows (PowerShell)
irm https://claude.ai/install.ps1 | iex

claude --version
claude            # first run → log in with the Claude Pro account
```

If install fails, check https://docs.claude.com for the current instructions for your OS.

---

## Phase 2 — Clone the repo and drop in the config files (~10 min, one person)

```bash
git clone https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project.git
cd Veritas-AI-Project
```

Copy these files from this bundle into the repo root, **exactly at these paths**:

| File | Where | What it does |
|---|---|---|
| `CLAUDE.md` | repo root | Claude reads this automatically every session: rules, judging criteria, stack, schedule |
| `.claude/settings.json` | repo root, inside `.claude/` folder | Permissions (what Claude may run without asking), safety denies, hooks, plugin list |
| `README.md` | repo root | Official write-up template — judges read this. Fill it in as you go |
| `CREDITS.md` | repo root | Every dataset / model / tutorial / AI tool with links (rule 3) |
| `.gitignore` | repo root | Keeps `.env`, big data and model artifacts out of git |
| `Makefile` | repo root | `make data / train / eval / demo / api` so the whole pipeline is one command |

Then:

```bash
# fill in CLAUDE.md §0 (track, project, what you add) — do this NOW
git add CLAUDE.md .claude/settings.json README.md CREDITS.md .gitignore Makefile
git commit -m "chore: add Claude Code config, write-up template, credits"
git push
```

Everyone else: `git pull`. The config is now shared — all three laptops get the same rules.

---

## Phase 3 — Install plugins (~5 min, each laptop)

Open Claude Code inside the repo (`cd Veritas-AI-Project && claude`) and run:

```
/plugin install superpowers@claude-plugins-official
/plugin install feature-dev@claude-plugins-official
/plugin install code-review@claude-plugins-official
/plugin install security-guidance@claude-plugins-official
/plugin install commit-commands@claude-plugins-official
/plugin install context7@claude-plugins-official
```

Optional (only if you build the Next.js UI):
```
/plugin install frontend-design@claude-plugins-official
/plugin install chrome-devtools-mcp@claude-plugins-official
```

Optional memory across sessions (helpful over 35 hrs, but costs context):
```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

If a plugin name isn't found: `/plugin marketplace update claude-plugins-official` then retry.
Check it worked: `/plugin` → should list them as enabled. **Keep ≤ 6 enabled at a time**
(`/plugin` → toggle off anything you aren't using; each one eats context).

Also run `/init` once — it checks CLAUDE.md is picked up. Then type `/memory` to confirm
CLAUDE.md shows as the project file.

---

## Phase 4 — The working loop (repeat for every feature)

**One feature per Claude session. Always say which judging criterion it serves.**

Example first prompts, in order:

```
1. "Read CLAUDE.md. Create the repo layout from §5 with empty files, requirements.txt,
    Makefile targets, and .gitignore. Commit."

2. "Implement ml/data.py: download <dataset>, clean it, split once into
    data/processed/{train,val,test}.csv with seed 42 (stratified / by date as the briefs
    require). Add the dataset to CREDITS.md. Run `make data` and show me the row counts.
    Criterion: Technical execution."

3. "Implement ml/baseline.py (majority class / persistence) and ml/evaluate.py that prints
    baseline metrics on the TEST set and writes results/metrics.json. Use the metric the
    briefs require for our track. Criterion: Testing & honesty."

4. "Implement ml/train.py with <model>. Re-run make eval so metrics.json has baseline AND
    model side by side. Criterion: Technical execution."

5. "Implement ml/failures.py: dump 5–10 wrong test predictions with inputs and our best
    guess why to results/failures.md. Criterion: Testing & honesty."

6. "Implement api/main.py (FastAPI) with /health and /predict loading ml/artifacts/.
    Show me a curl example that works. Criterion: Demo & clarity."

7. "<THE THING WE ADD> — e.g. test the model on messages we wrote in our own language and
    report results separately. Criterion: Originality (20 pts)."

8. "Update README.md Results section from results/metrics.json and results/failures.md.
    Do not invent numbers."
```

Habits that keep Claude sharp over 35 hours:

- **Start each session with:** `Read CLAUDE.md and NOTES.md, then tell me the current state in
  3 lines before doing anything.`
- **End each session with:** `Update NOTES.md: what works, what's next, open bugs. Commit.`
- **Use `/clear`** between unrelated features — a fresh context beats a bloated one.
- **Use `/review`** (code-review plugin) before merging anything a teammate wrote.
- **Use `/commit`** (commit-commands) — small commits, plain messages.
- **If Claude hits the usage limit:** switch to another teammate's session, or use ChatGPT
  Plus for write-up/video script work in the meantime. Don't sit idle.
- **If stuck > 20 min on one bug:** `/clear`, paste the exact error, ask for the 3 most likely
  causes, test each. If stuck > 45 min on data loading: switch dataset (the briefs say so).

---

## Phase 5 — Schedule checkpoints (CT)

| By | Must be true | If not |
|---|---|---|
| Sat 1:30 PM | Track chosen, CLAUDE.md §0 filled, `make data` works | Switch dataset |
| Sat 6:00 PM | `make eval` prints baseline vs model on test | Simplify the model |
| Sat 11:00 PM | `/predict` works; README half-drafted; CREDITS.md current | Skip Next.js, plan Gradio |
| Sun 12:00 PM | "What we added" is built AND measured; demo runs end to end | **Switch to Gradio now** |
| Sun 6:00 PM | README done; failures.md done; video uploaded unlisted | Cut features, not the write-up |
| Sun 8:00 PM | **Submit a first version** | — |
| Sun 10:59 PM | Final resubmit | — |

---

## Phase 6 — Submission checklist (Sunday evening)

- [ ] Repo is **public** (Settings → Danger zone → Change visibility). Test in an incognito window.
- [ ] `README.md` follows the official template headings exactly (see repo README).
- [ ] Health/Finance: disclaimer sentence present verbatim in README.
- [ ] `CREDITS.md` lists every dataset, pretrained model, tutorial, library, **Claude Code and
      ChatGPT** — with links. Copy the list into the form's Credits field too.
- [ ] Results in README match `results/metrics.json` — no rounding up, no invented numbers.
- [ ] At least one failure example in README with your explanation.
- [ ] Video ≤ 2 min, YouTube unlisted or Drive "anyone with link". Test in incognito.
- [ ] Form: track, every teammate's full name / email / school spelled exactly right.
- [ ] "What we added" stated on the form and in README.
- [ ] Rules Confirmation box: you can honestly tick every line.
- [ ] Submit by **8 PM CT**, then resubmit if you improve. Latest version is judged.
- [ ] If the form breaks: email contact@veritasai.com immediately with code + write-up links.

---

## What's in `.claude/settings.json` (so you can explain it to judges if asked)

- **permissions.allow** — commands Claude can run without prompting: python, pip, make,
  git add/commit/push, npm. Speeds everything up.
- **permissions.deny** — things Claude can never do: read `.env`, force-push, `reset --hard`,
  delete `data/` `results/` `ml/artifacts/`, `sudo`.
- **hooks.PostToolUse** — after Claude edits a `.py` file it's syntax-checked; `.ts/.tsx` are
  auto-formatted with prettier if present.
- **hooks.PreToolUse** — before a `git commit`, warns if ML code or requirements changed but
  `CREDITS.md` didn't (rule 3: cite everything).
- **hooks.Stop** — when a session ends with uncommitted changes, reminds you to commit.
- **enabledPlugins** — the six plugins from Phase 3, so every teammate gets the same set after
  `git pull` (they still need to run the `/plugin install` lines once).

Needs `jq` installed for the hooks (`brew install jq` / `sudo apt install jq` /
`winget install jqlang.jq`). If `jq` is missing the hooks just do nothing — nothing breaks.
