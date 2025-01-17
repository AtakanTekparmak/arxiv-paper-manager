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
    def get_importance_select(paper: Paper) -> Select:
        importance_colors = {
            "Low": "#8B8B8B",
            "Medium": "#FFA500",
            "High": "#FF4444"
        }
        current_color = importance_colors[paper.importance]
        
        return Select(
            Option("Low", value="Low", selected=paper.importance=="Low"),
            Option("Medium", value="Medium", selected=paper.importance=="Medium"),
            Option("High", value="High", selected=paper.importance=="High"),
            name="importance",
            hx_post=f"/update_importance/{paper.id}",
            hx_target=f"#paper-{paper.id}",
            hx_swap="outerHTML",
            style=f"""
            position: absolute;
            top: 10px;
            left: 10px;
            padding: 2px 5px;
            border-radius: 5px;
            background-color: {current_color};
            color: white;
            border: none;
            font-size: 0.8rem;
            width: 90px;
            cursor: pointer;
            """
        )

    def get_card_bottom(paper: Paper) -> Div:
        return Div(
            A("View PDF", href=paper.pdf_url, target="_blank"),
            Button("Remove", cls="remove-button", hx_delete=f"/remove/{paper.id}", hx_target="closest .card", hx_swap="outerHTML"),
            Button("Toggle State", cls="toggle-state-button", hx_post=f"/toggle_state/{paper.id}", hx_target="closest .card", hx_swap="outerHTML"),
            cls="card-bottom"
        )

    return Card(
        get_importance_select(paper),
        Div(paper.state, cls=f"paper-state {'to-be-read' if paper.state == 'To Be Read' else 'read'}"),
        H3(paper.title, cls="paper-title"),
        P(paper.abstract[:200] + '...' if len(paper.abstract) > 200 else paper.abstract, cls="paper-abstract"),
        P(f"Submitted on: {paper.date_submitted}" if paper.date_submitted else "Submission date unknown", cls="paper-date"),
        get_card_bottom(paper),
        id=f"paper-{paper.id}",
        cls="paper-card card"
    )

def get_toggle_buttons(filter: str = 'all', importance_filter: str = 'all') -> Div:
    """
    Returns the toggle buttons to filter the papers and a save button.

    Args:
        filter (str): The state filter to apply.
        importance_filter (str): The importance filter to apply.
    Returns:
        Div: The toggle buttons and save button.
    """
    filter_colors = {
        "all": "#666666",
        "to-be-read": "#FFA500",
        "read": "#4CAF50"
    }
    importance_colors = {
        "all": "#666666",
        "Low": "#8B8B8B",
        "Medium": "#FFA500",
        "High": "#FF4444"
    }
    
    common_style = """
        padding: 5px 10px;
        border-radius: 10px;
        color: white;
        border: none;
        font-size: 0.8rem;
        display: inline-flex;
        align-items: center;
        height: 36px;
        line-height: 36px;
    """
    
    button_style = f"""
        {common_style}
        cursor: pointer;
        justify-content: center;
        min-height: 36px;
    """
    
    select_style = f"""
        {common_style}
        cursor: pointer;
        appearance: none;
        -webkit-appearance: none;
        background-image: url("data:image/svg+xml;charset=US-ASCII,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20width%3D%22292.4%22%20height%3D%22292.4%22%3E%3Cpath%20fill%3D%22%23FFFFFF%22%20d%3D%22M287%2069.4a17.6%2017.6%200%200%200-13-5.4H18.4c-5%200-9.3%201.8-12.9%205.4A17.6%2017.6%200%200%200%200%2082.2c0%205%201.8%209.3%205.4%2012.9l128%20127.9c3.6%203.6%207.8%205.4%2012.8%205.4s9.2-1.8%2012.8-5.4L287%2095c3.5-3.5%205.4-7.8%205.4-12.8%200-5-1.9-9.2-5.4-12.8z%22%2F%3E%3C%2Fsvg%3E");
        background-repeat: no-repeat;
        background-position: right 8px center;
        background-size: 8px;
        padding-right: 25px;
        width: auto;
        min-height: 36px;
    """
    
    return Div(
        Button(
            "Add",
            cls="add-button",
            hx_get="/add_paper_form",
            hx_target="body",
            hx_swap="beforeend",
            style=f"{button_style} background-color: #4CAF50;"
        ),
        Button(
            "Save",
            cls="save-button",
            hx_post="/save",
            hx_swap="none",
            style=f"{button_style} background-color: #4a90e2;"
        ),
        Select(
            Option("State", value="all", selected=filter=="all"),
            Option("To Be Read", value="to-be-read", selected=filter=="to-be-read"),
            Option("Read", value="read", selected=filter=="read"),
            name="filter",
            hx_get="/",
            hx_target="body",
            hx_trigger="change",
            hx_include="[name='filter'], [name='importance_filter']",
            style=f"{select_style} background-color: {filter_colors[filter]};"
        ),
        Select(
            Option("Importance", value="all", selected=importance_filter=="all"),
            Option("Low", value="Low", selected=importance_filter=="Low"),
            Option("Medium", value="Medium", selected=importance_filter=="Medium"),
            Option("High", value="High", selected=importance_filter=="High"),
            name="importance_filter",
            hx_get="/",
            hx_target="body",
            hx_trigger="change",
            hx_include="[name='filter'], [name='importance_filter']",
            style=f"{select_style} background-color: {importance_colors[importance_filter]};"
        ),
        cls="toggle-buttons",
        style="""
        display: flex;
        gap: 10px;
        align-items: center;
        height: 36px;
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
            background-color: #ffa500;
            color: white;
            padding: 5px 10px;
            border-radius: 10px;
            """
        ),
        Span(
            f"Read: {read_count}", 
            cls="read-count",
            style="""
            background-color: #4CAF50;
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

def get_add_paper_form() -> Div:
    return Div(
        Div(
            Button(
                "×",
                cls="close-button",
                hx_get="/close_add_paper_form",
                hx_target="#add-paper-modal",
                hx_swap="outerHTML"
            ),
            H2("Add Paper", style="margin: 0;color: #041c26;"),
            cls="form-header",
            style="""
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
            """
        ),
        Form(
            Input(id="title", name="title", placeholder="Title", required=True),
            Textarea(id="abstract", name="abstract", placeholder="Abstract", required=True, rows=5),
            Input(id="pdf_url", name="pdf_url", placeholder="PDF URL", required=True),
            Input(id="date_submitted", name="date_submitted", placeholder="Date Submitted (DD MMM YYYY)", required=True),
            Button("Add Paper", type="submit"),
            cls="add-paper-form",
            hx_post="/add_paper",
            hx_target="body",
            hx_swap="beforeend"
        ),
        id="add-paper-form",
        cls="modal-content",
        style="""
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        max-width: 500px;
        width: 100%;
        """
    )

def get_add_paper_modal() -> Div:
    return Div(
        get_add_paper_form(),
        cls="modal",
        id="add-paper-modal",
        style="""
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background-color: rgba(0, 0, 0, 0.5);
        backdrop-filter: blur(5px);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
        """
    )