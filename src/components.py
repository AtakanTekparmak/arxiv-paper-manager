from fasthtml.common import *

from src.db import Paper, get_paper_count_by_state

def get_search_form(q: str = '') -> Form:
    """
    Returns a search form with the search input field pre-filled with the query.

    Args:
        q (str): The search query.
    Returns:
        Form: The search form.
    """
    return Form(
        Input(id="search", name="q", placeholder="Search papers...", value=q, type="search",
            hx_get="/",
            hx_trigger="search, keyup[key=='Enter']",
            hx_target="body"),
        Button("Search"),
        cls="search-form",
        method="get"
    )

def get_add_form() -> Form:
    """
    Returns a form to add a new paper to the database.

    Returns:
        Form: The add form
    """
    return Form(
        Input(id="url", name="url", placeholder="ArXiv URL", type="search"),
        Button("Add Paper"),
        cls="add-form search-form",
        hx_post="/add",
        hx_target="#paper-list",
        hx_swap="afterbegin"
    )

def get_paper_card(paper: Paper) -> Card:
    """
    Returns a card containing the paper information.

    Args:
        paper (Paper): The paper object.
    Returns:
        Card: The paper card.
    """ 
    def get_card_bottom(paper: Paper) -> Div:
        return Div(
            A("View PDF", href=paper.pdf_url, target="_blank"),
            Button("Remove", cls="remove-button", hx_delete=f"/remove/{paper.id}", hx_target="closest .card", hx_swap="outerHTML"),
            Button("Toggle State", cls="toggle-state-button", hx_post=f"/toggle_state/{paper.id}", hx_target="closest .card", hx_swap="outerHTML"),
            cls="card-bottom"
        )
    return Card(
        Div(paper.state, cls=f"paper-state {'to-be-read' if paper.state == 'To Be Read' else 'read'}"),
        H3(paper.title, cls="paper-title"),
        P(paper.abstract[:200] + '...' if len(paper.abstract) > 200 else paper.abstract, cls="paper-abstract"),
        P(f"Submitted on: {paper.date_submitted}" if paper.date_submitted else "Submission date unknown", cls="paper-date"),
        get_card_bottom(paper),
        id=f"paper-{paper.id}",
        cls="paper-card card"
    )

def get_toggle_buttons(filter: str) -> Div:
    """
    Returns the toggle buttons to filter the papers and a save button.

    Args:
        filter (str): The filter to apply.
    Returns:
        Div: The toggle buttons and save button.
    """
    return Div(
        Button(
            "Save",
            cls="save-button",
            hx_post="/save",
            hx_swap="none",
            style="""
            background-color: #4a90e2;
            border-color: #4a90e2;
            border-radius: 10px;
            display: flex;
            align-items: center;
            gap: 5px;
            """
        ),
        Button("To Be Read", 
               cls=f"to-be-read-button {'active' if filter == 'to-be-read' else ''}",
               id="to-be-read-toggle",
               hx_get=f"/?filter={'all' if filter == 'to-be-read' else 'to-be-read'}",
               hx_target="body",
               hx_push_url="true",
               style=f"""
               background-color: {'#e69400' if filter == 'to-be-read' else '#ffa500'};
               border-color: {'#e69400' if filter == 'to-be-read' else '#ffa500'};
               border-radius: 10px;
               """
        ),
        Button("Read", 
               cls=f"read-button {'active' if filter == 'read' else ''}",
               id="read-toggle",
               hx_get=f"/?filter={'all' if filter == 'read' else 'read'}",
               hx_target="body",
               hx_push_url="true",
               style=f"""
               background-color: {'#45a049' if filter == 'read' else '#4CAF50'};
               border-color: {'#45a049' if filter == 'read' else '#4CAF50'};
               border-radius: 10px;
               """
        ),
        cls="toggle-buttons",
        style="""
        display: flex;
        gap: 10px;
        """
    )

def get_paper_counts() -> Div:
    """
    Returns a Div containing the counts of papers by state.

    Returns:
        Div: The paper counts div.
    """
    to_be_read_count, read_count = get_paper_count_by_state()
    
    return Div(
        Span(
            f"To Be Read: {to_be_read_count}", 
            cls="to-be-read-count",
            style="""
            background-color: #4CAF50;
            color: white;
            padding: 5px 10px;
            border-radius: 10px;
            """
        ),
        Span(
            f"Read: {read_count}", 
            cls="read-count",
            style="""
            background-color: #ffa500;
            color: white;
            padding: 5px 10px;
            border-radius: 10px;
            """
        ),
        cls="paper-counts",
        style="""
        display: flex;
        gap: 10px;  
        align-items: center;
        """
    )