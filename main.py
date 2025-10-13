from fasthtml.common import *
import arxiv
import re
import json
from datetime import datetime
from pathlib import Path

# Simple CSS
css = Style("""
    body { font-family: system-ui; line-height: 1.6; max-width: 1400px; margin: 0 auto; padding: 20px; background: #f8fafc; }
    .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .header-content { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 20px; }
    .stats { display: flex; gap: 20px; flex-wrap: wrap; }
    .stat { text-align: center; padding: 10px; background: #f1f5f9; border-radius: 6px; min-width: 100px; }
    .stat-number { font-size: 24px; font-weight: bold; color: #3b82f6; }
    .stat-label { font-size: 12px; color: #64748b; }
    .controls { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .form-group { margin-bottom: 15px; }
    .form-group label { display: block; margin-bottom: 5px; font-weight: 600; }
    .form-input, select.form-input { width: 100%; padding: 10px; border: 2px solid #e2e8f0; border-radius: 6px; font-size: 16px; box-sizing: border-box; }
    .form-input:focus, select.form-input:focus { outline: none; border-color: #3b82f6; }
    .form-row { display: flex; gap: 10px; align-items: end; }
    .form-row .form-group { flex: 1; margin-bottom: 0; }
    .form-row .form-group:has(select) { flex: 0 0 auto; }
    .form-row button { flex: 0 0 auto; width: auto; }
    .btn { padding: 10px 20px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; text-decoration: none; margin: 5px; display: inline-block; transition: all 0.2s ease; }
    .btn:hover { opacity: 0.9; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
    .btn:active { transform: translateY(0); box-shadow: 0 1px 3px rgba(0,0,0,0.12); opacity: 0.95; }
    .btn-primary { background: #3b82f6; color: white; }
    .btn-secondary { background: #f1f5f9; color: #1e293b; border: 1px solid #e2e8f0; }
    .btn-success { background: #10b981; color: white; }
    .btn-danger { background: #ef4444; color: white; }
    .btn-save { background: #8b5cf6; color: white; }
    .btn:disabled, .btn.loading { opacity: 0.6; cursor: not-allowed; pointer-events: none; }
    form[hx-post] button[type="submit"]:active::after, form button[type="submit"]:active::after { content: "..."; }
    .filters { display: flex; gap: 10px; margin-top: 15px; flex-wrap: wrap; }
    .papers { display: grid; gap: 20px; grid-template-columns: 1fr; }
    @media (min-width: 768px) {
        .papers { grid-template-columns: repeat(2, 1fr); }
    }
    .paper-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
    .paper-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; color: #1e293b; }
    .paper-meta { font-size: 14px; color: #64748b; margin-bottom: 10px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
    .paper-abstract { color: #64748b; margin-bottom: 15px; line-height: 1.6; flex-grow: 1; }
    .paper-actions { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
    .status-read { background: rgba(16, 185, 129, 0.1); color: #10b981; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .status-unread { background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .importance-low { background: rgba(100, 116, 139, 0.1); color: #64748b; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .importance-medium { background: rgba(59, 130, 246, 0.1); color: #3b82f6; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .importance-high { background: rgba(239, 68, 68, 0.1); color: #ef4444; padding: 4px 8px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .alert { padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); font-weight: 500; display: flex; align-items: center; gap: 10px; }
    .alert-success { background: white; color: #10b981; border-left: 4px solid #10b981; }
    .alert-error { background: white; color: #ef4444; border-left: 4px solid #ef4444; }
    .alert-icon { font-size: 24px; }
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
        importance=str,
        pk='id'
    )
else:
    # Migration: Add importance column if it doesn't exist
    try:
        # Check if importance column exists by trying to query it
        papers(limit=1)
        existing_columns = [col[1] for col in db.execute("PRAGMA table_info(papers)").fetchall()]
        if 'importance' not in existing_columns:
            db.execute("ALTER TABLE papers ADD COLUMN importance TEXT DEFAULT 'Medium'")
            print("✅ Added 'importance' column to existing database")
    except Exception as e:
        print(f"Migration check: {e}")

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

def get_papers_filtered(search_query="", read_filter="all", importance_filter="all"):
    """Get filtered papers"""
    where_conditions = []
    
    if search_query:
        where_conditions.append(f"(title LIKE '%{search_query}%' OR abstract LIKE '%{search_query}%' OR authors LIKE '%{search_query}%')")
    
    if read_filter == "read":
        where_conditions.append("is_read = 1")
    elif read_filter == "unread":
        where_conditions.append("is_read = 0")
    
    if importance_filter and importance_filter != "all":
        # Capitalize first letter to match database format
        importance_val = importance_filter.capitalize()
        where_conditions.append(f"importance = '{importance_val}'")
    
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
                Form(
                    Button("💾 Save to JSON", type="submit", cls="btn btn-save"),
                    method="post",
                    action="/save_json"
                ),
                style="display: flex; align-items: center; gap: 20px; flex-wrap: wrap;"
            ),
            cls="header-content"
        ),
        cls="header"
    )

def controls_component(search_query="", current_filter="all", importance_filter="all"):
    return Div(
        # ArXiv URL form
        Form(
            Div(
                Label("Add ArXiv Paper by URL", cls="form-label"),
                Div(
                    Div(
                        Input(
                            type="url",
                            name="url",
                            placeholder="https://arxiv.org/abs/2301.00001 or ArXiv ID",
                            cls="form-input",
                            required=True
                        ),
                        cls="form-group"
                    ),
                    Div(
                        Label("Importance", cls="form-label"),
                        Select(
                            Option("Low", value="Low"),
                            Option("Medium", value="Medium", selected=True),
                            Option("High", value="High"),
                            name="importance",
                            cls="form-input"
                        ),
                        cls="form-group",
                        style="min-width: 150px;"
                    ),
                    Button("Add Paper", type="submit", cls="btn btn-primary"),
                    cls="form-row"
                ),
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
                Div(
                    Label("Importance", cls="form-label"),
                    Select(
                        Option("Low", value="Low"),
                        Option("Medium", value="Medium", selected=True),
                        Option("High", value="High"),
                        name="importance",
                        cls="form-input"
                    ),
                    cls="form-group"
                ),
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
            Div(
                Strong("Read Status: ", style="margin-right: 10px; color: #64748b;"),
                A("All", href=f"/?importance={importance_filter}", cls=f"btn {'btn-primary' if current_filter == 'all' else 'btn-secondary'}"),
                A("Unread", href=f"/?filter=unread&importance={importance_filter}", cls=f"btn {'btn-primary' if current_filter == 'unread' else 'btn-secondary'}"),
                A("Read", href=f"/?filter=read&importance={importance_filter}", cls=f"btn {'btn-primary' if current_filter == 'read' else 'btn-secondary'}"),
                style="display: flex; align-items: center; flex-wrap: wrap; margin-bottom: 10px;"
            ),
            Div(
                Strong("Importance: ", style="margin-right: 10px; color: #64748b;"),
                A("All", href=f"/?filter={current_filter}", cls=f"btn {'btn-primary' if importance_filter == 'all' else 'btn-secondary'}"),
                A("Low", href=f"/?filter={current_filter}&importance=low", cls=f"btn {'btn-primary' if importance_filter == 'low' else 'btn-secondary'}"),
                A("Medium", href=f"/?filter={current_filter}&importance=medium", cls=f"btn {'btn-primary' if importance_filter == 'medium' else 'btn-secondary'}"),
                A("High", href=f"/?filter={current_filter}&importance=high", cls=f"btn {'btn-primary' if importance_filter == 'high' else 'btn-secondary'}"),
                style="display: flex; align-items: center; flex-wrap: wrap;"
            ),
            cls="filters"
        ),
        
        cls="controls"
    )

def paper_card(paper):
    importance = getattr(paper, 'importance', 'Medium') or 'Medium'
    importance_class = f"importance-{importance.lower()}"
    
    return Div(
        H3(paper.title, cls="paper-title"),
        Div(
            Span(
                "✅ Read" if paper.is_read else "📖 Unread",
                cls=f"{'status-read' if paper.is_read else 'status-unread'}"
            ),
            Span(
                f"🔥 {importance}",
                cls=importance_class
            ),
            Span(
                f"👤 {paper.authors}",
                style="color: #64748b;"
            ) if paper.authors else None,
            Span(
                f"📅 {paper.published}",
                style="color: #64748b;"
            ) if paper.published else None,
            Span(
                f"🏷️ {paper.arxiv_id}",
                style="color: #64748b;"
            ) if paper.arxiv_id else None,
            cls="paper-meta"
        ),
        Div(
            paper.abstract[:300] + "..." if len(paper.abstract) > 300 else paper.abstract,
            cls="paper-abstract"
        ) if paper.abstract else "",
        Div(
            A("📄 PDF", href=paper.pdf_url, target="_blank", cls="btn btn-secondary") if paper.pdf_url else None,
            A("🔗 View", href=paper.url, target="_blank", cls="btn btn-secondary") if paper.url else None,
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
        "paper_added": "Paper added successfully!",
        "paper_deleted": "Paper deleted successfully!",
        "json_saved": "Database saved to arxiv_papers.json successfully!"
    }
    return Div(
        Span("✅", cls="alert-icon"),
        Span(messages.get(message, message)),
        cls="alert alert-success"
    )

def error_alert(error):
    messages = {
        "invalid_url": "Invalid ArXiv URL or ID format",
        "paper_not_found": "Paper not found on ArXiv",
        "database_error": "Database error occurred",
        "title_required": "Paper title is required"
    }
    return Div(
        Span("❌", cls="alert-icon"),
        Span(messages.get(error, error)),
        cls="alert alert-error"
    )

def get_next_json_id() -> int:
    """Get the next available ID for the JSON file"""
    json_file = "arxiv_papers.json"
    
    if not Path(json_file).exists():
        return 1
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        if not papers_data:
            return 1
        
        # Handle dict format with string keys
        if isinstance(papers_data, dict):
            max_id = max(int(k) for k in papers_data.keys())
            return max_id + 1
        # Handle array format
        else:
            max_id = max(int(paper.get('id', 0)) for paper in papers_data)
            return max_id + 1
    except:
        return 1

def save_paper_to_json(paper_data: dict):
    """Save a paper to the arxiv_papers.json file"""
    json_file = "arxiv_papers.json"
    
    try:
        # Read existing data
        if Path(json_file).exists():
            with open(json_file, 'r', encoding='utf-8') as f:
                papers_data = json.load(f)
                # Handle both dict and array formats
                if not isinstance(papers_data, dict):
                    papers_data = {}
        else:
            papers_data = {}
        
        # Get next ID
        next_id = get_next_json_id()
        
        # Convert database format to JSON format
        json_paper = {
            "id": str(next_id),
            "title": paper_data.get('title', ''),
            "authors": paper_data.get('authors', '').split(", ") if paper_data.get('authors') else [],
            "abstract": paper_data.get('abstract', ''),
            "url": paper_data.get('url', ''),
            "pdf_url": paper_data.get('pdf_url', ''),
            "submitted": paper_data.get('published', '') if paper_data.get('published') else datetime.now().strftime("%Y-%m-%d"),
            "read": paper_data.get('is_read', False),
            "source": "arxiv" if paper_data.get('arxiv_id') else "manual",
            "importance": paper_data.get('importance', 'Medium')
        }
        
        # Add new paper with string key
        papers_data[str(next_id)] = json_paper
        
        # Write back to file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Paper saved to {json_file}: '{json_paper['title'][:50]}...'")
        
    except Exception as e:
        print(f"❌ Error saving paper to JSON: {e}")

def update_paper_status_in_json(paper_id: int, is_read: bool):
    """Update paper read status in the JSON file"""
    json_file = "arxiv_papers.json"
    
    if not Path(json_file).exists():
        return
    
    try:
        # Get the paper from database to match with JSON
        paper = papers[paper_id]
        
        # Read JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        # Handle dict format
        if isinstance(papers_data, dict):
            # Find and update the matching paper in JSON
            for key, json_paper in papers_data.items():
                # Match by title and arxiv_id if available
                title_match = json_paper.get('title', '').strip() == paper.title.strip()
                arxiv_match = True
                if paper.arxiv_id and json_paper.get('pdf_url'):
                    extracted_id = extract_arxiv_id(json_paper.get('pdf_url', ''))
                    arxiv_match = extracted_id == paper.arxiv_id
                
                if title_match and arxiv_match:
                    json_paper['read'] = is_read
                    break
        
        # Write back to file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(papers_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Updated paper status in JSON: '{paper.title[:50]}...' -> {'Read' if is_read else 'Unread'}")
        
    except Exception as e:
        print(f"❌ Error updating paper status in JSON: {e}")

def delete_paper_from_json(paper_id: int):
    """Delete paper from the JSON file"""
    json_file = "arxiv_papers.json"
    
    if not Path(json_file).exists():
        return
    
    try:
        # Get the paper from database before deletion
        paper = papers[paper_id]
        
        # Read JSON data
        with open(json_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
        
        # Handle dict format
        if isinstance(papers_data, dict):
            # Find and remove the matching paper from JSON
            key_to_delete = None
            for key, json_paper in papers_data.items():
                title_match = json_paper.get('title', '').strip() == paper.title.strip()
                arxiv_match = True
                if paper.arxiv_id and json_paper.get('pdf_url'):
                    extracted_id = extract_arxiv_id(json_paper.get('pdf_url', ''))
                    arxiv_match = extracted_id == paper.arxiv_id
                
                if title_match and arxiv_match:
                    key_to_delete = key
                    break
            
            if key_to_delete:
                del papers_data[key_to_delete]
                
                # Write back to file
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(papers_data, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Deleted paper from JSON: '{paper.title[:50]}...'")
        
    except Exception as e:
        print(f"❌ Error deleting paper from JSON: {e}")

# Routes
@rt("/")
def get(search: str = "", filter: str = "all", importance: str = "all", success: str = "", error: str = ""):
    stats = get_stats()
    papers_list = get_papers_filtered(search, filter, importance)
    
    return Title("ArXiv Paper Manager"), Main(
        success_alert(success) if success else "",
        error_alert(error) if error else "",
        header_component(stats),
        controls_component(search, filter, importance),
        papers_section(papers_list, search)
    )

@rt("/add", methods=["POST"])
def post(url: str, importance: str = "Medium"):
    if not url.strip():
        return RedirectResponse("/?error=invalid_url", status_code=303)
    
    arxiv_id = extract_arxiv_id(url)
    if not arxiv_id:
        return RedirectResponse("/?error=invalid_url", status_code=303)
    
    paper_data = fetch_arxiv_paper(arxiv_id)
    if not paper_data:
        return RedirectResponse("/?error=paper_not_found", status_code=303)
    
    # Add importance to paper data
    paper_data['importance'] = importance
    
    try:
        papers.insert(paper_data)
        save_paper_to_json(paper_data)
        return RedirectResponse("/?success=paper_added", status_code=303)
    except:
        return RedirectResponse("/?error=database_error", status_code=303)

@rt("/add_manual", methods=["POST"])
def post(title: str, authors: str = "", url: str = "", abstract: str = "", importance: str = "Medium"):
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
        'added_date': datetime.now().isoformat(),
        'importance': importance
    }
    
    try:
        papers.insert(paper_data)
        save_paper_to_json(paper_data)
        return RedirectResponse("/?success=paper_added", status_code=303)
    except:
        return RedirectResponse("/?error=database_error", status_code=303)

@rt("/toggle_read/{paper_id}")
def post(paper_id: int):
    try:
        paper = papers[paper_id]
        new_status = not paper.is_read
        # Update using direct SQL
        db.execute("UPDATE papers SET is_read = ? WHERE id = ?", (new_status, paper_id))
        update_paper_status_in_json(paper_id, new_status)
    except Exception as e:
        print(f"Error toggling read status: {e}")
    return RedirectResponse("/", status_code=303)

@rt("/delete/{paper_id}")
def post(paper_id: int):
    try:
        delete_paper_from_json(paper_id)
        papers.delete(paper_id)
        return RedirectResponse("/?success=paper_deleted", status_code=303)
    except:
        return RedirectResponse("/?error=database_error", status_code=303)

@rt("/save_json", methods=["POST"])
def post():
    """Export all papers from database to arxiv_papers.json"""
    json_file = "arxiv_papers.json"
    
    try:
        # Get all papers from database
        all_papers = list(papers(order_by="added_date ASC"))
        
        # Convert to JSON format (dict with string keys)
        papers_dict = {}
        for idx, paper in enumerate(all_papers, 1):
            # Extract arxiv_id from pdf_url if arxiv_id is empty
            arxiv_id = paper.arxiv_id
            if not arxiv_id and paper.pdf_url:
                arxiv_id = extract_arxiv_id(paper.pdf_url)
            
            papers_dict[str(idx)] = {
                "id": str(idx),
                "title": paper.title,
                "authors": paper.authors.split(", ") if paper.authors else [],
                "abstract": paper.abstract,
                "url": paper.url,
                "pdf_url": paper.pdf_url,
                "submitted": paper.published if paper.published else datetime.now().strftime("%Y-%m-%d"),
                "read": paper.is_read,
                "source": "arxiv" if arxiv_id else "manual",
                "importance": getattr(paper, 'importance', 'Medium') or 'Medium'
            }
        
        # Write to file
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(papers_dict, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(papers_dict)} papers to {json_file}")
        return RedirectResponse(f"/?success=json_saved", status_code=303)
        
    except Exception as e:
        print(f"❌ Error saving to JSON: {e}")
        return RedirectResponse("/?error=database_error", status_code=303)

if __name__ == "__main__":
    serve()