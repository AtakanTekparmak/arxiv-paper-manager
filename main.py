from fasthtml.common import *
from starlette.staticfiles import StaticFiles
import requests
from bs4 import BeautifulSoup
import re

# Database setup
db = database('data/arxiv_papers.db')
papers = db.t.papers
if papers not in db.t:
    papers.create(id=int, title=str, abstract=str, pdf_url=str, state=str, pk='id')
Paper = papers.dataclass()

# Helper functions
def parse_arxiv_url(url):
    arxiv_id = re.search(r'(\d{4}\.\d{5})', url).group(1)
    return f"https://arxiv.org/abs/{arxiv_id}"

def fetch_paper_info(url):
    response = requests.get(parse_arxiv_url(url))
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1', class_='title mathjax').text.strip().replace('Title:', '').strip()
    abstract = soup.find('blockquote', class_='abstract mathjax').text.strip().replace('Abstract:', '').strip()
    pdf_url = f"https://arxiv.org/pdf/{re.search(r'(\d{4}\.\d{5})', url).group(1)}.pdf"
    return Paper(title=title, abstract=abstract, pdf_url=pdf_url, state="To Be Read")

def search_papers(query, all_papers):
    query = query.lower()
    return [p for p in all_papers if query in p.title.lower() or query in p.abstract.lower()]

# FastHTML app setup
app = FastHTML(
    hdrs=(
        picolink,
        Link(rel="stylesheet", href="/static/styles.css")
    )
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

rt = app.route

@rt("/")
def get(q: str = ''):
    search_form = Form(
        Input(id="search", name="q", placeholder="Search papers...", value=q),
        Button("Search"),
        cls="search-form",
        method="get"
    )
    
    add_form = Form(
        Input(id="url", name="url", placeholder="ArXiv URL"),
        Button("Add Paper"),
        cls="add-form",
        hx_post="/add",
        hx_target="#paper-list",
        hx_swap="afterbegin"
    )
    
    all_papers = list(papers())  # Fetch all papers from the database
    
    if q:
        results = search_papers(q, all_papers)
    else:
        results = sorted(all_papers, key=lambda p: p.id, reverse=True)
    
    paper_cards = [create_paper_card(paper) for paper in results]
    
    return Title("ArXiv Paper Manager"), Container(
        H1("ArXiv Paper Manager", cls="main-title"),
        search_form,
        add_form,
        Div(*paper_cards, id="paper-list", cls="paper-list")
    )

def create_paper_card(paper):
    return Card(
        Div(paper.state, cls=f"paper-state {'to-be-read' if paper.state == 'To Be Read' else 'read'}"),
        H3(paper.title, cls="paper-title"),
        P(paper.abstract[:200] + '...' if len(paper.abstract) > 200 else paper.abstract, cls="paper-abstract"),
        A("View PDF", href=paper.pdf_url, target="_blank"),
        Button("Remove", cls="remove-button", hx_delete=f"/remove/{paper.id}", hx_target="closest .card", hx_swap="outerHTML"),
        Button("Toggle State", cls="toggle-state-button", hx_post=f"/toggle_state/{paper.id}", hx_target="closest .card", hx_swap="outerHTML"),
        id=f"paper-{paper.id}",
        cls="paper-card card"
    )

@rt("/add")
def post(url: str):
    try:
        paper_info = fetch_paper_info(url)
        new_paper = papers.insert(paper_info)
        return Div(
            create_paper_card(new_paper),
            Input(id="url", name="url", placeholder="ArXiv URL", value="", hx_swap_oob="true"),
        )
    except Exception as e:
        return Div(f"Error adding paper: {str(e)}", cls="error-message")

@rt("/remove/{paper_id}")
def delete(paper_id: int):
    papers.delete(paper_id)
    return ""  # Return empty string to remove the card

@rt("/toggle_state/{paper_id}")
def post(paper_id: int):
    paper = papers[paper_id]
    new_state = "Read" if paper.state == "To Be Read" else "To Be Read"
    updated_paper = papers.update({"state": new_state}, paper_id)
    return create_paper_card(updated_paper)

serve()