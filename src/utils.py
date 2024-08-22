import requests
from bs4 import BeautifulSoup
import re

from src.db import Paper

def parse_arxiv_url(url: str) -> str:
    """
    Parses the ArXiv URL to get the arXiv ID
    """
    arxiv_id = re.search(r'(\d{4}\.\d{5})', url).group(1)
    return f"https://arxiv.org/abs/{arxiv_id}"

def fetch_paper_info(url: str) -> Paper:
    """
    Fetches the paper title, abstract, and PDF URL 
    from the ArXiv URL and returns a Paper object.
    """
    # Fetch the HTML content of the ArXiv URL
    response = requests.get(parse_arxiv_url(url))

    # Parse the HTML content using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('h1', class_='title mathjax').text.strip().replace('Title:', '').strip()
    abstract = soup.find('blockquote', class_='abstract mathjax').text.strip().replace('Abstract:', '').strip()
    pdf_url = f"https://arxiv.org/pdf/{re.search(r'(\d{4}\.\d{5})', url).group(1)}.pdf"
    #submitted = re.search(r'\d{1,2} \w{3} \d{4}', soup.find('div', class_='dateline').text.strip().split('Submitted on ')[1].strip()).group(0)

    return Paper(title=title, abstract=abstract, pdf_url=pdf_url)