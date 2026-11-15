# QA report — poll 1 (2026-11-14, ~22:45 CT)

Checks run against each agent's committed branch tip, not their status lines.
Branches: RANKING `agents-ranking.md-review`, FAILURES `failures.md-instructions`,
WRITEUP `writeup.md-instructions`, SUBMIT `submit.md-instructions`, DEMO `demo.md-execute`.

| # | Check | Result | Severity | Owner |
|---|---|---|---|---|
| 1 | Secrets: `git log -p --all` key grep = 0, tree grep empty, `.env` gitignored + untracked | PASS | — | — |
| 2 | All commits inside the window (earliest fef9392, Nov 14 12:12 CT = 13:12 ET) | PASS | — | — |
| 3 | `make test` on main, RANKING export, FAILURES export | PASS (18 passed each) | — | — |
| 4 | `make app` starts on committed code | **FAIL**: `TypeError: NativePlot.__init__() got an unexpected keyword argument 'overlay_point'` (Gradio 6). DEMO's uncommitted fix runs fine from worcester on :7860 | HIGH | DEMO: commit it |
| 5 | README states cleanest_3_overlap finding | PASS on WRITEUP branch (model 0.473 < persistence 0.483, stated as the headline). FAIL on main: README is still the blank template | HIGH until merged | human (merge) |
| 6 | Every README number traces to results/ | PASS: metrics.json, ranking_diagnosis.json (18/20/67 days, CI −0.051..+0.035, corr 0.829/0.789), failures.md (18–48 g, 45%, 414→366, wind 3.0→8.4%), raw CSV (25,176 rows, 22,626/2,529 split, 228–488, mean 359) | — | — |
| 7 | No TODO / [PENDING] | README (WRITEUP): 3 × [PENDING] for rank variants; row names `model_rank` don't exist; RANKING produced `model_deviation` (0.406) and `model_deviation_today_mean` (0.444), headline "NO VARIANT BEATS PERSISTENCE". failures.md (FAILURES): 0 TODO. SUBMISSION: human fields only | MED | WRITEUP once RANKING marks done |
| 8 | CREDITS complete | Libraries fixed on WRITEUP branch (numpy, joblib, uvicorn, pydantic, gradio, pytest, httpx, uv). ChatGPT "used for" still a placeholder | MED | human |
| 9 | Integration: judges read GitHub `main` | **Nothing merged or pushed.** Trial merge (`git merge-tree`): only `coordination/status.md` conflicts (trivial). No agent touched a shared file | HIGH | human |
| 10 | SUBMISSION rules box "every commit dated Nov 14 2026" | Inaccurate: evening commits are Nov 15 UTC and Sunday work is still coming. Say "Nov 14–15" | LOW | SUBMIT |
| 11 | Variants scored on the test set (rank.py) | All variants are reported, they all lose, and validation scores exist, so this is honest. README should say all variants are shown, none picked by test score | LOW | WRITEUP |
| 12 | Smoke tests for ml/rank.py, ml/failures.py (CLAUDE.md §10) | Missing. tests/** is read-only to agents | LOW | human, optional |

## Open human-only items
- Confirm "every team member listed contributed" (SUBMISSION rules box).
- ChatGPT "used for:", or remove the line if nobody used it.
- 3 team rows (name / email / school), submitter fields, "New to AI?", demo video URL.
- Merge all agent branches into `main` and push.
