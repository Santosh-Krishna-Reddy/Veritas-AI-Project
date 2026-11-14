# How to push this to GitHub (one person, ~3 minutes)

The repo https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project is currently empty.

## Option A — plain files (no git knowledge needed)

```bash
git clone https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project.git
cd Veritas-AI-Project
# unzip veritas-gridgreen-repo.zip, then copy EVERYTHING inside the unzipped folder
# (including the hidden .claude/ and .gitignore) into this directory
git add -A
git commit -m "chore: scaffold GridGreen — Claude Code config, ML pipeline, tests"
git push -u origin main
```

Windows tip: hidden files (`.claude`, `.gitignore`) don't copy if you drag-select in
Explorer. Use `xcopy /E /H unzipped\* .` in a terminal, or enable "Show hidden items".

## Option B — git bundle (keeps the original commit)

```bash
git clone https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project.git
cd Veritas-AI-Project
git pull /full/path/to/veritas-scaffold.bundle main
git push -u origin main
```

## Then, on every laptop

```bash
git pull
pip install -r requirements.txt
make test                       # expect: 9 passed
python -m ml.data --synthetic   # fake data, just to prove the pipeline runs
make train && make eval         # numbers printed are SYNTHETIC — not reportable
claude                          # start Claude Code; it reads CLAUDE.md automatically
```

Then run the six `/plugin install` lines from SETUP-GUIDE.md Phase 3.

## Check it worked

Open https://github.com/Santosh-Krishna-Reddy/Veritas-AI-Project in a private window.
You should see CLAUDE.md, README.md, ml/, api/, tests/. Delete this file afterwards
(`git rm PUSH-INSTRUCTIONS.md`) — it's not part of the submission.
