import json
from src.db import database, Paper, init_db

def load_papers_from_json(filename='arxiv_papers.json'):
    """
    Loads papers from a JSON file and inserts them into the database.

    Args:
        filename (str): The name of the JSON file to load.
    """
    try:
        # Initialize the database
        init_db()
        
        # Connect to the database
        db = database('data/arxiv_papers.db')
        papers = db.t.papers

        # Load the JSON file
        with open(filename, 'r') as f:
            paper_data = json.load(f)

        # Insert new papers with importance defaulting to Medium if not present
        success_count = 0
        for paper in paper_data:
            if 'importance' not in paper:
                paper['importance'] = 'Medium'
            try:
                papers.insert(Paper(**paper).model_dump(exclude={'id'}))
                success_count += 1
            except Exception as e:
                print(f"Error loading paper '{paper.get('title', 'Unknown Title')}': {str(e)}")

        print(f"Successfully loaded {success_count} out of {len(paper_data)} papers from {filename}")
    except FileNotFoundError:
        print(f"Warning: {filename} not found. Starting with empty database.")
    except json.JSONDecodeError:
        print(f"Error: {filename} is not a valid JSON file.")
    except Exception as e:
        print(f"Error loading papers: {str(e)}")
        raise

if __name__ == "__main__":
    load_papers_from_json()