from fasthtml.common import *
from starlette.staticfiles import StaticFiles

from src.db import init_db, add_paper, remove_paper, toggle_paper_state, get_all_papers, search_papers, Paper, save_db_as_json, get_paper_count_by_state, update_paper_importance
from src.utils import fetch_paper_info
from src.components import get_search_form, get_add_form, get_paper_card, get_toggle_buttons, get_paper_counts, get_add_paper_modal, get_add_paper_form

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
            get_paper_counts(),
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
            return Div(
                "Paper already exists in the database.", 
                cls="error-message",
                style="""
                color: #721c24;
                """
            )
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

@rt("/save")
def post():
    try:
        save_db_as_json()
        return Div(
            "Database saved successfully", 
        )
    except Exception as e:
        return Div(
            f"Error saving database: {str(e)}"
        )

@rt("/add_paper_form")
def get():
    return get_add_paper_modal()

@rt("/close_add_paper_form")
def get():
    return ""

@rt("/add_paper")
def post(title: str, abstract: str, pdf_url: str, date_submitted: str):
    new_paper = add_paper(Paper(title=title, abstract=abstract, pdf_url=pdf_url, date_submitted=date_submitted, state="To Be Read"))
    if new_paper is None:
        return Div(
            "Paper already exists in the database.",
            cls="error-message",
            style="""
            color: #721c24;
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            border-radius: 5px;
            padding: 10px;
            margin-top: 10px;
            """
        )
    return Div(
        get_paper_card(Paper(**new_paper)),
        Script("document.querySelector('.modal').remove();"),
        hx_swap_oob="afterbegin:#paper-list"
    )

@rt("/update_importance/{paper_id}")
def post(paper_id: int, importance: str):
    """
    Updates the importance of a paper.
    """
    try:
        updated_paper = update_paper_importance(paper_id, importance)
        return get_paper_card(updated_paper)
    except ValueError as e:
        return Div(f"Error updating importance: {str(e)}", cls="error-message")

serve()