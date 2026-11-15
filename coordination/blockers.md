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

## [SUBMIT] 2026-11-14 — URGENT
What I was doing: checking each Rules Confirmation line in SUBMISSION.md against the repo.
What blocked me: two lines can't honestly be ticked yet.
  1. "Every dataset, library, tutorial and AI tool credited in CREDITS.md" is FALSE today.
     requirements.txt uses numpy, joblib, uvicorn, pydantic, gradio, pytest, httpx; none of
     them are in CREDITS.md. The uv installer (used by the Makefile) is missing too. ChatGPT's
     "used for:" is still a placeholder. Owner: WRITEUP (CREDITS.md).
  2. "Every team member listed contributed": only a human can confirm this.
What I need from the human: WRITEUP fixes CREDITS.md (or a human does). A human confirms
  line 2 and fills the human-only fields: submitter name/school/email, 3 team rows,
  "New to AI?", demo video URL.
What I did instead while waiting: left both boxes unticked (☐) with a note. Once CREDITS.md is
  fixed, tick line 1 in SUBMISSION.md. Also noted for WRITEUP/FAILURES: the README is still the
  blank template (the Write-up Link points at it), and every "Why" in results/failures.md is TODO.
Security: clean. No .env tracked, 0 key-shaped strings in git history. The repo is PUBLIC
  (gh API + unauthenticated HTTP 200).
