# Set default target
.DEFAULT_GOAL := help

# Variables

## Python
PYTHON := python3
PIP := pip
VENV_NAME := venv

# .env file
ENV_FILE := .env

# Help target
help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  1. install           Install dependencies and set up the environment (should be run first)"
	@echo "  2. load_papers       Load papers from JSON file"
	@echo "  3. run               Run the main.py script"
	@echo "  4. clean             Remove the virtual environment and its contents"
	@echo "  5. reset_db          Delete the database (will prompt for confirmation)"
	@echo "  6. backup_db         Create a backup of the current database"
	@echo "  7. init_db           Initialize an empty database with the current schema"

# Install dependencies and set up the environment
install: 
	$(PYTHON) -m venv $(VENV_NAME)
	. $(VENV_NAME)/bin/activate && \
	$(PIP) install -r requirements.txt 

# Load papers from JSON file
load_papers:
	. $(VENV_NAME)/bin/activate && \
	$(PYTHON) load_papers.py

# Run the main.py script
run: 
	. $(VENV_NAME)/bin/activate && \
	$(PYTHON) main.py

# Clean the virtual environment
clean:
	rm -rf $(VENV_NAME)

# Reset the database
reset_db:
	@echo "Are you sure you want to delete the database? [y/N] " && read ans && [ $${ans:-N} = y ]
	rm -f data/arxiv_papers.db
	@echo "Database deleted. Run 'make load_papers' to reload from JSON."

# Backup the current database
backup_db:
	@mkdir -p backups
	@cp data/arxiv_papers.db "backups/arxiv_papers_$(shell date +%Y%m%d_%H%M%S).db"
	@echo "Database backed up to backups/"

# Initialize empty database
init_db:
	. $(VENV_NAME)/bin/activate && \
	$(PYTHON) -c "from src.db import init_db; init_db()"