.PHONY: help install deploy analyze clean test lint format

help:
	@echo "Available targets:"
	@echo "  install  - Install Python dependencies"
	@echo "  deploy   - Deploy monitoring stack to Kubernetes"
	@echo "  analyze  - Run probe analysis"
	@echo "  clean    - Clean generated files"
	@echo "  test     - Run tests"
	@echo "  lint     - Run linters"
	@echo "  format   - Format code"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

deploy:
	kubectl apply -f monitoring/probe-metrics-exporter.yaml
	@echo "Monitoring stack deployed. Wait 24-48h for data collection."

analyze:
	python scripts/analyze-prometheus-metrics.py

audit:
	./scripts/audit-exec-probes.sh

clean:
	rm -f probe-analysis-report*.json
	rm -f apply-patches-*.sh
	rm -f prometheus-probe-analysis-*.json
	rm -f remediation-report-*.json
	rm -f gke-1.35-probe-audit-*.md
	rm -f gke-1.35-probe-audit-*.json

test:
	pytest tests/ -v --cov=scripts

lint:
	flake8 scripts/
	mypy scripts/

format:
	black scripts/
