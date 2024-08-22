import json
from src.db import database, Paper, init_db

def load_papers_from_json(filename='arxiv_papers.json'):
    """
    Loads papers from a JSON file and inserts them into the database.

    Args:
        filename (str): The name of the JSON file to load.
    """
    # Initialize the database
    init_db()
    
    # Connect to the database
    db = database('data/arxiv_papers.db')
    papers = db.t.papers

    # Load the JSON file
    with open(filename, 'r') as f:
        paper_data = json.load(f)

    # Insert new papers
    for paper in paper_data:
        papers.insert(Paper(**paper).model_dump(exclude={'id'}))

    print(f"Loaded {len(paper_data)} papers from {filename}")

if __name__ == "__main__":
    load_papers_from_json()