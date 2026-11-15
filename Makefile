# Python interpreter.
#
# We point straight at the venv interpreter so nothing needs `source activate`
# and `make` works from any shell. Build that venv with uv:
#
#     brew install uv
#     uv venv --python 3.12
#     uv pip install -r requirements.txt
#
# Why uv and not pip: Homebrew's bundled pip (every version, 3.12 and 3.14 alike)
# crashes on macOS 26 because its vendored truststore parses an empty
# platform.mac_ver() string. uv is a standalone binary with no such dependency.
#
# Override if your setup differs:  make train PY=python3.12
PY ?= .venv/bin/python

.PHONY: install fetch data train eval experiments rank decision figures failures demo api app test all pipeline check

install:
	uv pip install -r requirements.txt

check:
	$(PY) -c "import sklearn, pandas, fastapi, gradio, joblib; print('deps ok')"
	$(PY) -c "import ml.config as C; print('region:', C.REGION_NAME)"

test:
	$(PY) -m pytest -q tests/

fetch:
	$(PY) -m ml.fetch

data:
	$(PY) -m ml.data

train:
	$(PY) -m ml.train

eval:
	$(PY) -m ml.evaluate

experiments:
	@if [ -f results/ablation.json ] && [ -f ml/artifacts/model_v2_lo.joblib ] && [ -f ml/artifacts/model_v2_hi.joblib ]; then echo "experiments: using locked test-once results"; else $(PY) -m ml.experiments; fi

rank:
	$(PY) -m ml.rank

decision:
	@if [ -f ml/decision.py ]; then $(PY) -m ml.decision; else echo "decision skipped: ml/decision.py missing"; fi

figures:
	@if [ -f ml/figures.py ]; then $(PY) -m ml.figures; else echo "figures skipped: ml/figures.py missing"; fi

failures:
	$(PY) -m ml.failures

demo:
	$(PY) -m ml.demo

api:
	$(PY) -m uvicorn api.main:app --reload --port 8000

app:
	$(PY) -m app

# Everything from raw download to metrics, in order. Start here on a fresh clone.
pipeline: fetch data train eval rank failures

all: data train eval experiments rank decision figures failures
