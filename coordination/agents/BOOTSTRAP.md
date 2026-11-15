# BOOTSTRAP — get the GridGreen scaffolding onto origin/main

Work in this worktree's repo root. Do the steps in order and report each result.
Do not ask the human anything unless step 3 or 4 fails.

The main checkout lives at /Users/santoshreddy/Veritas-AI-Project. It holds new,
uncommitted files that this worktree (branched from origin/main) does not have.

1. Copy the new files in from the main checkout. NEVER copy .env.
       SRC=/Users/santoshreddy/Veritas-AI-Project
       cp "$SRC"/app.py "$SRC"/SUBMISSION.md "$SRC"/QUICKSTART.md "$SRC"/conductor.json "$SRC"/Makefile .
       mkdir -p .claude coordination
       cp -R "$SRC"/coordination/. coordination/
       cp "$SRC"/.claude/settings.json .claude/settings.json
   (If any source file is missing, say which and continue.)
2. rm -f Makefile.new Makefile_v2 Makefile_v3 claude-settings.json
3. SECRET CHECK:
       grep -rIlE '(EIA_API_KEY|api_key)=[A-Za-z0-9]{20,}' . --exclude=.env --exclude-dir=.git --exclude-dir=.venv --exclude-dir=node_modules
       git log -p --all | grep -cE '(EIA_API_KEY|api_key)=[A-Za-z0-9]{20,}'
   The grep must print nothing and the git log count must be 0. (The pattern matches any
   real key assignment without containing any part of our key.) If ANY other file matches,
   STOP and report the filename. Do not commit.
4. git check-ignore .env   -> must print ".env". If not, STOP and report.
5. git add -A, then show `git status --short`. Confirm .env is NOT staged.
6. git commit -m "Add demo app, coordination scaffolding, uv Makefile, conductor setup, agent permissions"
7. git push origin HEAD:main
8. Report the commit hash and whether the push succeeded. If the push fails on
   authentication, show the exact error and stop — the human will sign in.
