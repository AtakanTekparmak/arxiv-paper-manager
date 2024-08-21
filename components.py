from fasthtml.common import *

from db import Paper

def get_search_form(q: str = '') -> Form:
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
    return Form(
        Input(id="url", name="url", placeholder="ArXiv URL", type="search"),
        Button("Add Paper"),
        cls="add-form search-form",
        hx_post="/add",
        hx_target="#paper-list",
        hx_swap="afterbegin"
    )

def get_paper_card(paper: Paper) -> Card:
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