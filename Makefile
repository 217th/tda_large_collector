PYTHON ?= python3
PYTHONPATH := src

install:
	$(PYTHON) -m pip install -r requirements.txt -r requirements-dev.txt

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -q

docker-build:
	docker build -t tda-collector .

run-live:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m tda_collector --mode=live --config=./config.yaml

run-history:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m tda_collector --mode=history --config=./config.yaml --start=2023-01-01T00:00:00Z --end=2023-01-02T00:00:00Z

