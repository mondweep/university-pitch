.PHONY: help install test lint format clean validate enrich-all deploy

# Default target
help:
	@echo "LBS Knowledge Graph - Makefile Commands"
	@echo "=========================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install           - Install dependencies"
	@echo "  make setup             - Initial project setup"
	@echo ""
	@echo "Development:"
	@echo "  make test              - Run all tests"
	@echo "  make lint              - Run linting checks"
	@echo "  make format            - Format code"
	@echo "  make clean             - Clean generated files"
	@echo ""
	@echo "Phase 3 - Semantic Enrichment:"
	@echo "  make enrich-all        - Run complete enrichment pipeline"
	@echo "  make enrich-sentiment  - Run sentiment analysis only"
	@echo "  make enrich-topics     - Run topic extraction only"
	@echo "  make enrich-ner        - Run NER extraction only"
	@echo "  make enrich-personas   - Run persona classification only"
	@echo "  make enrich-similarity - Run similarity calculation only"
	@echo "  make enrich-clustering - Run topic clustering only"
	@echo ""
	@echo "Validation & Quality:"
	@echo "  make validate-phase1   - Validate Phase 1 (graph structure)"
	@echo "  make validate-phase2   - Validate Phase 2 (relationships)"
	@echo "  make validate-phase3   - Validate Phase 3 (enrichments)"
	@echo "  make validate-all      - Run all validations"
	@echo "  make quality-report    - Generate quality metrics report"
	@echo ""
	@echo "Cost Management:"
	@echo "  make cost-report       - Generate cost usage report"
	@echo "  make check-budget      - Check if budget allows enrichment"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-dev        - Deploy to development"
	@echo "  make deploy-prod       - Deploy to production"
	@echo "  make backup            - Create data backup"
	@echo "  make restore           - Restore from backup"
	@echo ""

# ============================================
# Setup & Installation
# ============================================

install:
	pip install --upgrade pip
	pip install -r requirements.txt

setup: install
	@echo "Setting up project structure..."
	mkdir -p data/raw data/processed data/graph data/checkpoints data/costs data/backups
	mkdir -p logs
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file - please configure it"; \
	fi
	@echo "Setup complete!"

# ============================================
# Development
# ============================================

test:
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

lint:
	flake8 src/ tests/ scripts/
	pylint src/ tests/ scripts/
	mypy src/

format:
	black src/ tests/ scripts/
	isort src/ tests/ scripts/

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf data/checkpoints/*.json

# ============================================
# Phase 3 - Semantic Enrichment
# ============================================

enrich-all:
	@echo "Running complete enrichment pipeline..."
	python scripts/full_pipeline.py \
		--graph data/graph/graph.json \
		--output data/graph/graph_enriched.json \
		--checkpoint-dir data/checkpoints

enrich-sentiment:
	python scripts/enrich_sentiment.py \
		--graph data/graph/graph.json \
		--output data/checkpoints/graph_with_sentiment.json \
		--batch-size 50

enrich-topics:
	python scripts/enrich_topics.py \
		--graph data/checkpoints/graph_with_sentiment.json \
		--output data/checkpoints/graph_with_topics.json \
		--batch-size 50

enrich-ner:
	python scripts/enrich_ner.py \
		--graph data/checkpoints/graph_with_topics.json \
		--output data/checkpoints/graph_with_ner.json \
		--batch-size 50

enrich-personas:
	python scripts/enrich_personas.py \
		--graph data/checkpoints/graph_with_ner.json \
		--output data/checkpoints/graph_with_personas.json \
		--batch-size 50

enrich-similarity:
	python scripts/enrich_similarity.py \
		--graph data/checkpoints/graph_with_personas.json \
		--output data/checkpoints/graph_with_similarity.json \
		--threshold 0.7

enrich-clustering:
	python scripts/enrich_topic_clusters.py \
		--graph data/checkpoints/graph_with_similarity.json \
		--output data/graph/graph_enriched.json \
		--min-cluster-size 3

# ============================================
# Validation & Quality
# ============================================

validate-phase1:
	python src/validation/run_validation.py \
		--phase 1 \
		--graph data/graph/graph.json

validate-phase2:
	python src/validation/run_phase2_validation.py \
		--graph data/graph/graph.json

validate-phase3:
	python src/validation/run_phase3_validation.py \
		--graph data/graph/graph_enriched.json \
		--output validation_report.json

validate-all: validate-phase1 validate-phase2 validate-phase3

quality-report:
	python src/validation/graph_quality_metrics.py \
		--graph data/graph/graph_enriched.json \
		--output quality_report.json

# ============================================
# Cost Management
# ============================================

cost-report:
	python scripts/cost_report.py \
		--cost-dir data/costs \
		--output cost_report.json

check-budget:
	python scripts/check_budget.py \
		--graph data/graph/graph.json \
		--max-cost 50.00 \
		--output budget_report.json

# ============================================
# Deployment
# ============================================

deploy-dev:
	@echo "Deploying to development..."
	@# Add deployment commands here

deploy-prod:
	@echo "Deploying to production..."
	@echo "⚠️  WARNING: This will deploy to production!"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "Deploying..."; \
		# Add production deployment commands here
	fi

backup:
	@echo "Creating backup..."
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	mkdir -p data/backups/$$TIMESTAMP; \
	cp -r data/graph data/backups/$$TIMESTAMP/; \
	echo "Backup created at data/backups/$$TIMESTAMP"

restore:
	@echo "Available backups:"
	@ls -1 data/backups/
	@read -p "Enter backup timestamp to restore: " BACKUP; \
	if [ -d "data/backups/$$BACKUP" ]; then \
		cp -r data/backups/$$BACKUP/graph/* data/graph/; \
		echo "Restored from backup $$BACKUP"; \
	else \
		echo "Backup not found"; \
	fi

# ============================================
# Docker Support
# ============================================

docker-build:
	docker build -t lbs-knowledge-graph:latest .

docker-run:
	docker run -it --rm \
		-v $$(pwd)/data:/app/data \
		-v $$(pwd)/.env:/app/.env \
		lbs-knowledge-graph:latest

docker-test:
	docker run -it --rm lbs-knowledge-graph:latest make test

# ============================================
# CI/CD Support
# ============================================

ci-install:
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install pytest pytest-cov flake8 black isort mypy

ci-test: test lint

ci-validate: validate-all

ci-deploy:
	@echo "Running CI deployment..."
	# Add CI-specific deployment commands
