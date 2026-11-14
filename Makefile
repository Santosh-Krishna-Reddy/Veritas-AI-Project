.PHONY: data train eval failures demo api test all

test:
	pytest -q tests/

data:
	python -m ml.data

train:
	python -m ml.train

eval:
	python -m ml.evaluate

failures:
	python -m ml.failures

demo:
	python -m ml.demo

api:
	uvicorn api.main:app --reload --port 8000

all: data train eval failures
