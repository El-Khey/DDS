PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
VENV_FLASK := $(VENV)/bin/flask

DB := src/server/instance/refuge_climatique.sqlite
DELETE_SQL := src/server/schema/delete.sql

.DEFAULT_GOAL := help

.PHONY: help install run dev drop clean

help:
	@echo "Commandes disponibles :"
	@echo "  make install  Crée l'environnement Python et installe les dépendances"
	@echo "  make run      Lance l'application sur http://127.0.0.1:5000"
	@echo "  make dev      Lance l'application en mode debug"
	@echo "  make drop     Supprime les tables de la base de données"
	@echo "  make clean    Supprime uniquement les caches générés"
	@echo "  export ILAAS_API_KEY=\"clé_api_du_prof\""
	@echo "  puis vérifier avec: echo \"\$$ILAAS_API_KEY\""

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

install: $(VENV_PYTHON)
	$(VENV_PIP) install -r requirements.txt

run: install
	$(VENV_FLASK) --app src.server.app run

dev: install
	$(VENV_FLASK) --app src.server.app run --debug

drop:
	sqlite3 $(DB) < $(DELETE_SQL)

clean:
	find src -type f -name '*.py[co]' -delete 2>/dev/null || true
	find src -type d -name '__pycache__' -empty -delete 2>/dev/null || true
	rm -rf .pytest_cache