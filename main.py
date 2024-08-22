from fasthtml.common import *
from starlette.staticfiles import StaticFiles

from src.db import init_db, add_paper, remove_paper, toggle_paper_state, get_all_papers, search_papers, Paper
from src.utils import fetch_paper_info
from src.components import get_search_form, get_add_form, get_paper_card, get_toggle_buttons

# Initialize the database
init_db()

# FastHTML app setup
app = FastHTML(
    hdrs=(
        picolink,
        Link(rel="stylesheet", href="/static/styles.css"),
        Script(src="/static/main.js")
    )
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

rt = app.route

@rt("/")
def get(q: str = '', filter: str = 'all'):

    # Get the search form, add form, and paper cards
    search_form = get_search_form(q)
    add_form = get_add_form()
    
    if q:
        results = search_papers(q)
    else:
        results = get_all_papers(filter)
    
    paper_cards = [get_paper_card(paper) for paper in results]
    
    toggle_buttons = get_toggle_buttons(filter)
    
    return Title("ArXiv Paper Manager"), Container(
        Div(
            H1("ArXiv Paper Manager", cls="main-title"),
            toggle_buttons,
            cls="header"
        ),
        search_form,
        add_form,
        Div(*paper_cards, id="paper-list", cls="paper-list")
    )

@rt("/add")
def post(url: str):
    try:
        paper_info = fetch_paper_info(url)
        new_paper = add_paper(paper_info)
        if new_paper is None:
            return Div("Paper already exists in the database.", cls="error-message")
        return Div(
            get_paper_card(Paper(**new_paper)),
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
    return get_paper_card(updated_paper)

serve()