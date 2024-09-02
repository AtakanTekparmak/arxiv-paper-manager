import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

from src.db import Paper

class ArxivParsingError(Exception):
    pass

def parse_arxiv_url(url: str) -> str:
    """
    Parses the ArXiv URL to get the arXiv ID
    """
    # Check if the URL is from arxiv.org
    if not urlparse(url).netloc.endswith('arxiv.org'):
        raise ArxivParsingError("The provided URL is not from arxiv.org")
    
    match = re.search(r'(\d{4}\.\d{5})', url)
    if not match:
        raise ArxivParsingError("Could not find a valid ArXiv ID in the URL")
    
    arxiv_id = match.group(1)
    return f"https://arxiv.org/abs/{arxiv_id}"

def fetch_paper_info(url: str) -> Paper:
    """
    Fetches the paper title, abstract, and PDF URL 
    from the ArXiv URL and returns a Paper object.
    """
    try:
        # Fetch the HTML content of the ArXiv URL
        response = requests.get(parse_arxiv_url(url))
        response.raise_for_status()  # Raises an HTTPError for bad responses

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        title_elem = soup.find('h1', class_='title mathjax')
        abstract_elem = soup.find('blockquote', class_='abstract mathjax')
        date_elem = soup.find('div', class_='dateline')
        
        if not title_elem or not abstract_elem or not date_elem:
            raise ArxivParsingError("Could not find title, abstract, or date elements in the HTML")
        
        title = title_elem.text.strip().replace('Title:', '').strip()
        abstract = abstract_elem.text.strip().replace('Abstract:', '').strip()
        pdf_url = f"https://arxiv.org/pdf/{re.search(r'(\d{4}\.\d{5})', url).group(1)}.pdf"
        
        date_match = re.search(r'Submitted on (\d+ [A-Za-z]+ \d{4})', date_elem.text)
        date_submitted = date_match.group(1) if date_match else None

        return Paper(title=title, abstract=abstract, pdf_url=pdf_url, date_submitted=date_submitted)
    
    except requests.RequestException as e:
        raise ArxivParsingError(f"Failed to fetch the ArXiv page: {str(e)}")
    except (AttributeError, IndexError) as e:
        raise ArxivParsingError(f"Error parsing the ArXiv page: {str(e)}")