import requests
from bs4 import BeautifulSoup
import re
from db import Paper

def parse_arxiv_url(url):
    arxiv_id = re.search(r'(\d{4}\.\d{5})', url).group(1)
    return f"https://arxiv.org/abs/{arxiv_id}"

def fetch_paper_info(url):
    response = requests.get(parse_arxiv_url(url))
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1', class_='title mathjax').text.strip().replace('Title:', '').strip()
    abstract = soup.find('blockquote', class_='abstract mathjax').text.strip().replace('Abstract:', '').strip()
    pdf_url = f"https://arxiv.org/pdf/{re.search(r'(\d{4}\.\d{5})', url).group(1)}.pdf"
    return Paper(title=title, abstract=abstract, pdf_url=pdf_url)

def create_paper_card(paper):
    from fasthtml.common import Card, Div, H3, P, A, Button
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