from typing import Optional, Union
from datetime import datetime
import json

from fasthtml.common import database
from pydantic import BaseModel

# Database setup
db = database('data/arxiv_papers.db')
papers = db.t.papers

# Pydantic model for Paper
class Paper(BaseModel):
    id: Optional[int] = None
    title: str
    abstract: str
    pdf_url: str
    state: str = "To Be Read"
    priority: str = "Low"
    date_submitted: Optional[str] = None

# Initialize the database
def init_db():
    if papers not in db.t:
        papers.create(id=int, title=str, abstract=str, pdf_url=str, state=str, priority=str, date_submitted=str, pk='id')

# Database operations
def add_paper(paper: Paper) -> Union[None, int]:
    """
    Adds a new paper to the database.

    Args:
        paper (Paper): The Paper object to add.
    Returns:
        int: The ID of the added paper.
    """
    existing_papers = get_all_papers()
    for p in existing_papers:
        if p.title == paper.title:
            return None
    return papers.insert(paper.model_dump(exclude={'id'}))

def remove_paper(paper_id: int):
    """
    Removes a paper from the database.

    Args:
        paper_id (int): The ID of the paper.
    """ 
    papers.delete(paper_id)

def toggle_paper_state(paper_id: int):
    """
    Toggles the state of the paper between "To Be Read" and "Read".

    Args:
        paper_id (int): The ID of the paper.
    Returns:
        Paper: The updated Paper object.
    """
    paper_dict = papers[paper_id]
    paper = Paper(**paper_dict)
    new_state = "Read" if paper.state == "To Be Read" else "To Be Read"
    updated_paper = papers.update({"state": new_state}, paper_id)
    return Paper(**updated_paper)

def toggle_paper_priority(paper_id: int):
    """
    Toggles the priority of the paper between "Low" and "High".

    Args:
        paper_id (int): The ID of the paper.
    Returns:
        Paper: The updated Paper object.
    """
    paper_dict = papers[paper_id]
    paper = Paper(**paper_dict)
    new_priority = "High" if paper.priority == "Low" else "Low"
    updated_paper = papers.update({"priority": new_priority}, paper_id)
    return Paper(**updated_paper)

def get_all_papers(filter='all'):
    """
    Returns all papers in the database.

    Args:
        filter (str): The filter to apply.
    Returns:
        list: A list of Paper objects.
    """
    all_papers = [Paper(**p) for p in papers()]

    def parse_date(date_str):
        if not date_str:
            return datetime.min
        try:
            return datetime.strptime(date_str, "%d %b %Y")
        except ValueError:
            return datetime.min

    all_papers.sort(key=lambda x: parse_date(x.date_submitted), reverse=True)
    if filter == 'all':
        return all_papers
    elif filter == 'to-be-read':
        return [p for p in all_papers if p.state == "To Be Read"]
    elif filter == 'read':
        return [p for p in all_papers if p.state == "Read"]
    else:
        raise ValueError("Invalid filter value")

def search_papers(query: str):
    """
    Searches for papers containing the query in their title or abstract.

    Args:
        query (str): The search query.
    Returns:
        list: A list of Paper objects that match the query.
    """
    all_papers = get_all_papers()
    query = query.lower()
    return [p for p in all_papers if query in p.title.lower() or query in p.abstract.lower()]

def save_db_as_json():
    """
    Saves the database as a JSON file.
    """
    with open('arxiv_papers.json', 'w') as f:
        json.dump(papers(), f, indent=4)

def get_paper_count_by_state():
    """
    Returns the count of papers by state.

    Returns:
        tuple: A tuple containing the count of "To Be Read" and "Read" papers.
    """
    all_papers = get_all_papers()
    to_be_read_count = sum(1 for p in all_papers if p.state == "To Be Read")
    read_count = sum(1 for p in all_papers if p.state == "Read")
    return to_be_read_count, read_count