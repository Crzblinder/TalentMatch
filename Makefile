.PHONY: help install backend frontend test docker-up docker-down docker-up-ollama docker-down-ollama seed lint

help:
	@echo "Available targets:"
	@echo "  install          - Install backend and frontend dependencies"
	@echo "  backend          - Run backend development server"
	@echo "  frontend         - Run frontend development server"
	@echo "  seed             - Seed database with sample jobs, skills and companies"
	@echo "  test             - Run all tests"
	@echo "  docker-up        - Start full stack with Docker Compose (cloud API mode)"
	@echo "  docker-down      - Stop Docker Compose stack"
	@echo "  docker-up-ollama - Start full stack with local Ollama (no API key needed)"
	@echo "  docker-down-ollama - Stop Ollama stack"
	@echo "  lint             - Run linters"

install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

seed:
	cd backend && python scripts/seed_data.py

test:
	cd backend && pytest -q
	cd frontend && npm run test

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-up-ollama:
	docker compose -f docker-compose.yml -f docker-compose.ollama.yml up --build -d

docker-down-ollama:
	docker compose -f docker-compose.yml -f docker-compose.ollama.yml down

lint:
	cd backend && python -m ruff check app tests
	cd frontend && npm run lint
