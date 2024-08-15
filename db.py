from fasthtml.common import database
from pydantic import BaseModel
from typing import Optional

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

# Initialize the database
def init_db():
    if papers not in db.t:
        papers.create(id=int, title=str, abstract=str, pdf_url=str, state=str, pk='id')

# Database operations
def add_paper(paper: Paper):
    return papers.insert(paper.model_dump(exclude={'id'}))

def remove_paper(paper_id: int):
    papers.delete(paper_id)

def toggle_paper_state(paper_id: int):
    paper_dict = papers[paper_id]
    paper = Paper(**paper_dict)
    new_state = "Read" if paper.state == "To Be Read" else "To Be Read"
    updated_paper = papers.update({"state": new_state}, paper_id)
    return Paper(**updated_paper)

def get_all_papers(filter='all'):
    all_papers = [Paper(**p) for p in papers()]
    if filter == 'all':
        return all_papers
    elif filter == 'to-be-read':
        return [p for p in all_papers if p.state == "To Be Read"]
    elif filter == 'read':
        return [p for p in all_papers if p.state == "Read"]
    else:
        raise ValueError("Invalid filter value")

def search_papers(query: str):
    all_papers = get_all_papers()
    query = query.lower()
    return [p for p in all_papers if query in p.title.lower() or query in p.abstract.lower()]