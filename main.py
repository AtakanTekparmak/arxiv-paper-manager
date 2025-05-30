from fasthtml.common import *
import arxiv
import re
from datetime import datetime

# Simple CSS
css = Style("""
    body { font-family: system-ui; line-height: 1.6; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f8fafc; }
    .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .stats { display: flex; gap: 20px; }
    .stat { text-align: center; padding: 10px; background: #f1f5f9; border-radius: 6px; }
    .stat-number { font-size: 24px; font-weight: bold; color: #3b82f6; }
    .stat-label { font-size: 12px; color: #64748b; }
    .controls { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 600; }
    .form-input { width: 100%; padding: 10px; border: 2px solid #e2e8f0; border-radius: 6px; font-size: 16px; }
    .form-input:focus { outline: none; border-color: #3b82f6; }
    .btn { padding: 10px 20px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; text-decoration: none; margin: 5px; }
    .btn-primary { background: #3b82f6; color: white; }
    .btn-secondary { background: #f1f5f9; color: #1e293b; border: 1px solid #e2e8f0; }
    .btn-success { background: #10b981; color: white; }
    .btn-danger { background: #ef4444; color: white; }
    .filters { display: flex; gap: 10px; margin-top: 15px; }
    .papers { display: grid; gap: 20px; }
    .paper-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .paper-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #1e293b; }
    .paper-meta { font-size: 14px; color: #64748b; margin-bottom: 10px; }
    .paper-abstract { color: #64748b; margin-bottom: 15px; line-height: 1.6; }
    .paper-actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .status-read { background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 4px 8px; border-radius: 12px; font-size: 12px; }
    .status-unread { background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 4px 8px; border-radius: 12px; font-size: 12px; }
    .alert { padding: 15px; border-radius: 6px; margin-bottom: 20px; }
    .alert-success { background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); }
    .alert-error { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
    .empty-state { text-align: center; padding: 60px 20px; color: #64748b; }
    details { border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; margin: 10px 0; }
    summary { cursor: pointer; font-weight: 600; }
""")

# Database setup using FastLite
db = database('data/papers.db')
papers = db.t.papers
if papers not in db.t:
    papers.create(
        id=int, 
        arxiv_id=str, 
        title=str, 
        authors=str, 
        abstract=str, 
        published=str, 
        url=str, 
        pdf_url=str, 
        categories=str, 
        is_read=bool, 
        notes=str, 
        added_date=str,
        pk='id'
    )
Paper = papers.dataclass()

# App setup
app, rt = fast_app(hdrs=[css])

# Helper functions
def extract_arxiv_id(url: str):
    """Extract arXiv ID from various URL formats"""
    patterns = [
        r'arxiv\.org/abs/([^/?]+)',
        r'arxiv\.org/pdf/([^/?]+)',
        r'([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            arxiv_id = match.group(1)
            arxiv_id = re.sub(r'\.pdf$', '', arxiv_id)
            return arxiv_id
    return None

def fetch_arxiv_paper(arxiv_id: str):
    """Fetch paper details from arXiv API"""
    try:
        client = arxiv.Client()
        search = arxiv.Search(id_list=[arxiv_id])
        result = next(client.results(search), None)
        
        if result:
            return {
                'arxiv_id': arxiv_id,
                'title': result.title.strip(),
                'authors': ", ".join([author.name for author in result.authors]),
                'abstract': result.summary.strip(),
                'published': result.published.strftime("%Y-%m-%d"),
                'url': result.entry_id,
                'pdf_url': result.pdf_url,
                'categories': ", ".join(result.categories),
                'is_read': False,
                'notes': '',
                'added_date': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error fetching paper: {e}")
    return None

def get_stats():
    """Get paper statistics"""
    total = len(papers())
    read_papers = papers(where="is_read = 1")
    read = len(read_papers) if read_papers else 0
    unread = total - read
    return {"total": total, "read": read, "unread": unread}

def get_papers_filtered(search_query="", read_filter="all"):
    """Get filtered papers"""
    where_conditions = []
    
    if search_query:
        where_conditions.append(f"(title LIKE '%{search_query}%' OR abstract LIKE '%{search_query}%' OR authors LIKE '%{search_query}%')")
    
    if read_filter == "read":
        where_conditions.append("is_read = 1")
    elif read_filter == "unread":
        where_conditions.append("is_read = 0")
    
    where_clause = " AND ".join(where_conditions) if where_conditions else None
    
    try:
        result = papers(where=where_clause, order_by="added_date DESC")
        return result if result else []
    except:
        return list(papers())

# Components
def header_component(stats):
    return Div(
        Div(
            Div(
                Span("📚", style="font-size: 24px; margin-right: 10px;"),
                "ArXiv Paper Manager",
                style="display: flex; align-items: center; font-size: 24px; font-weight: bold; color: #3b82f6;"
            ),
            Div(
                Div(
                    Div(str(stats["total"]), cls="stat-number"),
                    Div("Total Papers", cls="stat-label"),
                    cls="stat"
                ),
                Div(
                    Div(str(stats["unread"]), cls="stat-number"),
                    Div("To Read", cls="stat-label"),
                    cls="stat"
                ),
                Div(
                    Div(str(stats["read"]), cls="stat-number"),
                    Div("Read", cls="stat-label"),
                    cls="stat"
                ),
                cls="stats"
            ),
            style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;"
        ),
        cls="header"
    )

def controls_component(search_query="", current_filter="all"):
    return Div(
        # ArXiv URL form
        Form(
            Div(
                Label("Add ArXiv Paper by URL", cls="form-label"),
                Input(
                    type="url",
                    name="url",
                    placeholder="https://arxiv.org/abs/2301.00001 or ArXiv ID",
                    cls="form-input",
                    required=True
                ),
                Button("Add Paper", type="submit", cls="btn btn-primary"),
                cls="form-group"
            ),
            method="post",
            action="/add"
        ),
        
        # Manual paper form
        Details(
            Summary("📝 Add Non-ArXiv Paper"),
            Form(
                Input(type="text", name="title", placeholder="Paper Title", cls="form-input", required=True),
                Input(type="text", name="authors", placeholder="Authors", cls="form-input"),
                Input(type="url", name="url", placeholder="Paper URL (optional)", cls="form-input"),
                Textarea(name="abstract", placeholder="Abstract (optional)", cls="form-input", rows="3"),
                Button("Add Manual Paper", type="submit", cls="btn btn-secondary"),
                method="post",
                action="/add_manual"
            )
        ),
        
        # Search form
        Form(
            Div(
                Label("Search Papers", cls="form-label"),
                Input(
                    type="text",
                    name="search",
                    placeholder="Search papers by title, abstract, or authors...",
                    value=search_query,
                    cls="form-input"
                ),
                Button("🔍 Search", type="submit", cls="btn btn-primary"),
                cls="form-group"
            ),
            method="get"
        ),
        
        # Filter buttons
        Div(
            A("All Papers", href="/", cls=f"btn {'btn-primary' if current_filter == 'all' else 'btn-secondary'}"),
            A("Unread", href="/?filter=unread", cls=f"btn {'btn-primary' if current_filter == 'unread' else 'btn-secondary'}"),
            A("Read", href="/?filter=read", cls=f"btn {'btn-primary' if current_filter == 'read' else 'btn-secondary'}"),
            cls="filters"
        ),
        
        cls="controls"
    )

def paper_card(paper):
    return Div(
        H3(paper.title, cls="paper-title"),
        Div(
            f"👤 {paper.authors}" if paper.authors else "",
            " | " if paper.authors and paper.published else "",
            f"📅 {paper.published}" if paper.published else "",
            " | " if (paper.authors or paper.published) and paper.arxiv_id else "",
            f"🏷️ {paper.arxiv_id}" if paper.arxiv_id else "",
            cls="paper-meta"
        ),
        Div(
            paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract,
            cls="paper-abstract"
        ) if paper.abstract else "",
        Div(
            Span(
                "✅ Read" if paper.is_read else "📖 Unread",
                cls=f"{'status-read' if paper.is_read else 'status-unread'}"
            ),
            A("📄 PDF", href=paper.pdf_url, target="_blank", cls="btn btn-secondary") if paper.pdf_url else "",
            A("🔗 View", href=paper.url, target="_blank", cls="btn btn-secondary") if paper.url else "",
            Form(
                Button("✅ Mark Read" if not paper.is_read else "📖 Mark Unread", 
                       type="submit", 
                       cls=f"btn {'btn-success' if not paper.is_read else 'btn-secondary'}"),
                method="post",
                action=f"/toggle_read/{paper.id}",
                style="display: inline;"
            ),
            Form(
                Button("🗑️ Delete", type="submit", cls="btn btn-danger",
                       onclick="return confirm('Are you sure?')"),
                method="post",
                action=f"/delete/{paper.id}",
                style="display: inline;"
            ),
            cls="paper-actions"
        ),
        cls="paper-card"
    )

def papers_section(papers_list, search_query=""):
    if not papers_list:
        return Div(
            Div("📄", style="font-size: 48px; margin-bottom: 20px;"),
            H3("No papers found"),
            P("Add some papers to get started!" if not search_query else f"No papers match '{search_query}'"),
            cls="empty-state"
        )
    
    return Div(
        *[paper_card(paper) for paper in papers_list],
        cls="papers"
    )

def success_alert(message):
    messages = {
        "paper_added": "✅ Paper added successfully!",
        "paper_deleted": "🗑️ Paper deleted successfully!"
    }
    return Div(messages.get(message, message), cls="alert alert-success")

def error_alert(error):
    messages = {
        "invalid_url": "❌ Invalid ArXiv URL or ID format",
        "paper_not_found": "❌ Paper not found on ArXiv",
        "database_error": "❌ Database error occurred",
        "title_required": "❌ Paper title is required"
    }
    return Div(messages.get(error, error), cls="alert alert-error")

# Routes
@rt("/")
def get(search: str = "", filter: str = "all", success: str = "", error: str = ""):
    stats = get_stats()
    papers_list = get_papers_filtered(search, filter)
    
    return Title("ArXiv Paper Manager"), Main(
        success_alert(success) if success else "",
        error_alert(error) if error else "",
        header_component(stats),
        controls_component(search, filter),
        papers_section(papers_list, search)
    )

@rt("/add", methods=["POST"])
def post(url: str):
    if not url.strip():
        return RedirectResponse("/?error=invalid_url", status_code=303)
    
    arxiv_id = extract_arxiv_id(url)
    if not arxiv_id:
        return RedirectResponse("/?error=invalid_url", status_code=303)
    
    paper_data = fetch_arxiv_paper(arxiv_id)
    if not paper_data:
        return RedirectResponse("/?error=paper_not_found", status_code=303)
    
    try:
        papers.insert(paper_data)
        return RedirectResponse("/?success=paper_added", status_code=303)
    except:
        return RedirectResponse("/?error=database_error", status_code=303)

@rt("/add_manual", methods=["POST"])
def post(title: str, authors: str = "", url: str = "", abstract: str = ""):
    if not title.strip():
        return RedirectResponse("/?error=title_required", status_code=303)
    
    paper_data = {
        'title': title.strip(),
        'authors': authors.strip(),
        'url': url.strip(),
        'abstract': abstract.strip(),
        'arxiv_id': '',
        'published': '',
        'pdf_url': '',
        'categories': '',
        'is_read': False,
        'notes': '',
        'added_date': datetime.now().isoformat()
    }
    
    try:
        papers.insert(paper_data)
        return RedirectResponse("/?success=paper_added", status_code=303)
    except:
        return RedirectResponse("/?error=database_error", status_code=303)

@rt("/toggle_read/{paper_id}")
def post(paper_id: int):
    try:
        paper = papers[paper_id]
        papers.update(paper_id, is_read=not paper.is_read)
    except:
        pass
    return RedirectResponse("/", status_code=303)

@rt("/delete/{paper_id}")
def post(paper_id: int):
    try:
        papers.delete(paper_id)
        return RedirectResponse("/?success=paper_deleted", status_code=303)
    except:
        return RedirectResponse("/?error=database_error", status_code=303)

if __name__ == "__main__":
    serve()