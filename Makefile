.PHONY: install run clean dev backup restore venv load_papers

# Python virtual environment
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# Create virtual environment
venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

# Install dependencies
install: venv
	$(PIP) install -r requirements.txt

# Run the application
run: install
	$(PYTHON) main.py

# Run in development mode with auto-reload
dev: install
	$(VENV)/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Clean up database and temporary files
clean:
	rm -f data/papers.db
	rm -f *.pyc
	rm -rf __pycache__
	rm -rf $(VENV)

# Reset database (clean slate)
reset_db:
	rm -f data/papers.db
	@echo "Database reset. Run 'make load_papers' to reload from JSON."

# Backup database
backup:
	mkdir -p backups
	cp data/papers.db backups/papers_backup_$(shell date +%Y%m%d_%H%M%S).db
	@echo "Database backed up to backups/ directory"

backup_db: backup

# Restore from backup (usage: make restore BACKUP=backups/papers_backup_20240101_120000.db)
restore:
	cp $(BACKUP) data/papers.db
	@echo "Database restored from $(BACKUP)"

# Show database stats
stats:
	@echo "=== Database Statistics ==="
	@sqlite3 data/papers.db "SELECT 'Total Papers: ', COUNT(*) FROM papers; SELECT 'Read Papers: ', COUNT(*) FROM papers WHERE is_read = 1; SELECT 'Unread Papers: ', COUNT(*) FROM papers WHERE is_read = 0; SELECT 'High Importance: ', COUNT(*) FROM papers WHERE importance = 'High'; SELECT 'Medium Importance: ', COUNT(*) FROM papers WHERE importance = 'Medium'; SELECT 'Low Importance: ', COUNT(*) FROM papers WHERE importance = 'Low';"

# Export papers to JSON
export:
	sqlite3 data/papers.db -json "SELECT * FROM papers ORDER BY added_date DESC;" > papers_export_$(shell date +%Y%m%d_%H%M%S).json
	@echo "Papers exported to papers_export_*.json"

# Load papers from JSON file
load_papers:
	$(PYTHON) load_papers.py

help:
	@echo "Available commands:"
	@echo "  venv         - Create Python virtual environment"
	@echo "  install      - Install Python dependencies (creates venv if needed)"
	@echo "  run          - Run the application"
	@echo "  dev          - Run in development mode with auto-reload"
	@echo "  load_papers  - Load papers from arxiv_papers.json file"
	@echo "  clean        - Remove database, temporary files, and virtual environment"
	@echo "  reset_db     - Reset database (remove data/papers.db)"
	@echo "  backup       - Create a timestamped backup of the database in backups/"
	@echo "  backup_db    - Alias for backup"
	@echo "  restore      - Restore from backup (specify BACKUP=backups/filename)"
	@echo "  stats        - Show database statistics including importance counts"
	@echo "  export       - Export papers to JSON file"
	@echo "  help         - Show this help message"