# SUBMIT agent — GridGreen

Read coordination/contracts.md FIRST. Owned: SUBMISSION.md only.

BEHAVIOR: Never guess human-only values (team names/emails/schools, video URL,
Space URL). Leave placeholders and note them once in coordination/blockers.md.

TASK
1. Update every claim in SUBMISSION.md to match README.md and results/metrics.json,
   including the cleanest_3_overlap finding in the pitch and "Anything Else".
2. Re-check each Rules Confirmation line against the repo; tick only what is true.
   Any line that can't honestly be ticked -> URGENT entry in coordination/blockers.md.
3. Security check, recorded in SUBMISSION.md's checklist:
       git ls-files | grep -E '^\.env$'          (expect nothing)
       git log -p --all | grep -cE '(EIA_API_KEY|api_key)=[A-Za-z0-9]{20,}'   (expect 0)
   Any hit -> URGENT blocker: the repo must be scrubbed before it's shared.
4. Check https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project is public.
   If web access is blocked, note it for the human to check in incognito.
5. Keep SUBMISSION.md copy-paste ready: the form fillable in under 10 minutes.

DONE WHEN only human-only fields remain and status.md reads
"SUBMIT: ready — awaiting <list>".
