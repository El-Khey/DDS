PYTHON ?= python3
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
VENV_FLASK := $(VENV)/bin/flask

DB := src/server/instance/refuge_climatique.sqlite
DELETE_SQL := src/server/schema/delete.sql
COUNT ?= 100
SEED ?= 1
SQL := src/server/data/peuplement.sql

.DEFAULT_GOAL := help

.PHONY: help install run dev populate verifier drop clean

help:
	@echo "Commandes disponibles :"
	@echo "  make install  Crée l'environnement Python et installe les dépendances"
	@echo "  make run      Lance l'application sur http://127.0.0.1:5000"
	@echo "  make dev      Lance l'application en mode debug"
	@echo "  make populate COUNT=100 SEED=1  Génère les factures et écrit $(SQL)"
	@echo "  make verifier Vérifie les exemples contre les schémas JSON, DTD et XSD"
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

populate: install
	$(VENV_PYTHON) -m src.server.scripts.populate --count $(COUNT) --seed $(SEED) --sql $(SQL)

verifier: install
	$(VENV_PYTHON) -m src.server.scripts.verifier_exemples

drop:
	$(VENV_PYTHON) -c "import sqlite3; sqlite3.connect('$(DB)').executescript(open('$(DELETE_SQL)').read())"

clean:
	find . -type f -name '*.py[co]' -not -path './$(VENV)/*' -delete
	find . -type d -name '__pycache__' -not -path './$(VENV)/*' -empty -delete
	rm -rf .pytest_cache
