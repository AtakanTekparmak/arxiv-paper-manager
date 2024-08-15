from fasthtml.common import *
from starlette.staticfiles import StaticFiles
from db import init_db, add_paper, remove_paper, toggle_paper_state, get_all_papers, search_papers, Paper
from utils import fetch_paper_info, create_paper_card

# Initialize the database
init_db()

# FastHTML app setup
app = FastHTML(
    hdrs=(
        picolink,
        Link(rel="stylesheet", href="/static/styles.css"),
        Script(src="/static/main.js")  # Add this line to include the JavaScript file
    )
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

rt = app.route

@rt("/")
def get(q: str = '', filter: str = 'all'):
    search_form = Form(
        Input(id="search", name="q", placeholder="Search papers...", value=q, type="search",
            hx_get="/",
            hx_trigger="search, keyup[key=='Enter']",
            hx_target="body"),
        Button("Search"),
        cls="search-form",
        method="get"
    )

    add_form = Form(
        Input(id="url", name="url", placeholder="ArXiv URL", type="search"),
        Button("Add Paper"),
        cls="add-form search-form",
        hx_post="/add",
        hx_target="#paper-list",
        hx_swap="afterbegin"
    )
    
    if q:
        results = search_papers(q)
    else:
        results = get_all_papers(filter)
    
    paper_cards = [create_paper_card(paper) for paper in results]
    
    return Title("ArXiv Paper Manager"), Container(
        H1("ArXiv Paper Manager", cls="main-title"),
        search_form,
        add_form,
        Div(*paper_cards, id="paper-list", cls="paper-list")
    )

@rt("/add")
def post(url: str):
    try:
        paper_info = fetch_paper_info(url)
        new_paper = add_paper(paper_info)
        return Div(
            create_paper_card(Paper(**new_paper)),
            Input(id="url", name="url", placeholder="ArXiv URL", value="", type="search", hx_swap_oob="true"),
        )
    except Exception as e:
        return Div(f"Error adding paper: {str(e)}", cls="error-message")

@rt("/remove/{paper_id}")
def delete(paper_id: int):
    remove_paper(paper_id)
    return "" 

@rt("/toggle_state/{paper_id}")
def post(paper_id: int):
    updated_paper = toggle_paper_state(paper_id)
    return create_paper_card(updated_paper)

serve()