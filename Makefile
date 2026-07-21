# Makefile for Rice Yield Forecasting
# Provides convenience targets for backend/frontend setup and local development.

.PHONY: help install install-backend install-frontend backend frontend

help:
	@echo "Rice Yield Forecasting Makefile"
	@echo "Usage: make <target>"
	@echo "  install           Install both backend and frontend dependencies"
	@echo "  install-backend   Install Python backend dependencies"
	@echo "  install-frontend  Install frontend dependencies"
	@echo "  backend           Start the FastAPI backend server"
	@echo "  frontend          Start the Vite frontend development server"
	@echo "  help              Show this help message"

install: install-backend install-frontend

install-backend:
	@echo "Installing backend dependencies..."
	python -m pip install -r backend/requirements.txt

install-frontend:
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

backend:
	@echo "Starting backend server..."
	cd backend && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

frontend:
	@echo "Starting frontend dev server..."
	cd frontend && npm run dev
