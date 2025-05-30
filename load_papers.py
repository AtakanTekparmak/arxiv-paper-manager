import json
import sys
import re
from datetime import datetime
from fastlite import database
from pathlib import Path

def extract_arxiv_id_from_url(url: str) -> str:
    """Extract arXiv ID from PDF URL"""
    if not url:
        return ""
    
    patterns = [
        r'arxiv\.org/pdf/([^/?]+)\.pdf',
        r'arxiv\.org/abs/([^/?]+)',
        r'([0-9]{4}\.[0-9]{4,5}(?:v[0-9]+)?)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            arxiv_id = match.group(1)
            # Remove .pdf extension if present
            arxiv_id = re.sub(r'\.pdf$', '', arxiv_id)
            return arxiv_id
    return ""

def convert_date(date_str: str) -> str:
    """Convert date string to ISO format"""
    if not date_str:
        return datetime.now().isoformat()
    
    try:
        # Try to parse "20 May 2022" format
        date_obj = datetime.strptime(date_str, "%d %b %Y")
        return date_obj.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # Try to parse "12 Jun 2024" format
            date_obj = datetime.strptime(date_str, "%d %b %Y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            # If parsing fails, return current date
            return datetime.now().strftime("%Y-%m-%d")

def convert_state_to_read(state: str) -> bool:
    """Convert state to boolean read status"""
    return state.lower() in ["read", "completed", "finished"]

def map_paper_data(paper_json: dict) -> dict:
    """Map JSON paper data to database schema"""
    pdf_url = paper_json.get("pdf_url", "")
    arxiv_id = extract_arxiv_id_from_url(pdf_url)
    
    # Create abstract URL from PDF URL if possible
    url = ""
    if arxiv_id:
        url = f"https://arxiv.org/abs/{arxiv_id}"
    
    return {
        'arxiv_id': arxiv_id,
        'title': paper_json.get("title", "").strip(),
        'authors': paper_json.get("authors", ""),  # Not in original JSON, will be empty
        'abstract': paper_json.get("abstract", "").strip(),
        'published': convert_date(paper_json.get("date_submitted", "")),
        'url': url,
        'pdf_url': pdf_url,
        'categories': paper_json.get("categories", ""),  # Not in original JSON
        'is_read': convert_state_to_read(paper_json.get("state", "")),
        'notes': f"Importance: {paper_json.get('importance', 'Not specified')}",
        'added_date': datetime.now().isoformat()
    }

def load_papers_from_json(json_file: str = "arxiv_papers.json"):
    """Load papers from JSON file into database"""
    
    # Check if JSON file exists
    if not Path(json_file).exists():
        print(f"Error: File '{json_file}' not found!")
        print("Please make sure the JSON file exists in the current directory.")
        return False
    
    # Initialize database (same as main app)
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
    
    # Load JSON data
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            papers_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in '{json_file}': {e}")
        return False
    except Exception as e:
        print(f"Error reading file '{json_file}': {e}")
        return False
    
    if not isinstance(papers_data, list):
        print(f"Error: JSON file should contain a list of papers")
        return False
    
    # Process each paper
    added_count = 0
    skipped_count = 0
    error_count = 0
    
    print(f"Loading {len(papers_data)} papers from '{json_file}'...")
    print("-" * 50)
    
    for i, paper_json in enumerate(papers_data, 1):
        try:
            # Map the data
            paper_data = map_paper_data(paper_json)
            
            # Check if paper already exists (by title or arxiv_id)
            existing = None
            if paper_data['arxiv_id']:
                try:
                    existing = papers(where=f"arxiv_id = '{paper_data['arxiv_id']}'")
                    existing = existing[0] if existing else None
                except:
                    pass
            
            if not existing and paper_data['title']:
                try:
                    escaped_title = paper_data['title'].replace("'", "''")
                    existing = papers(where=f"title = '{escaped_title}'")
                    existing = existing[0] if existing else None
                except:
                    pass
            
            if existing:
                print(f"  {i:2d}. SKIPPED: '{paper_data['title'][:60]}...' (already exists)")
                skipped_count += 1
            else:
                # Insert the paper
                papers.insert(paper_data)
                status = "✅ READ" if paper_data['is_read'] else "📖 UNREAD"
                print(f"  {i:2d}. ADDED ({status}): '{paper_data['title'][:50]}...'")
                added_count += 1
                
        except Exception as e:
            print(f"  {i:2d}. ERROR: Failed to process paper: {e}")
            error_count += 1
    
    # Print summary
    print("-" * 50)
    print(f"📊 SUMMARY:")
    print(f"   ✅ Added: {added_count} papers")
    print(f"   ⏭️  Skipped: {skipped_count} papers (already exist)")
    print(f"   ❌ Errors: {error_count} papers")
    print(f"   📝 Total processed: {len(papers_data)} papers")
    
    if added_count > 0:
        print(f"\n🎉 Successfully imported {added_count} new papers!")
        print(f"   Run 'make run' to start the paper manager and view your papers.")
    
    return True

def main():
    """Main function"""
    json_file = sys.argv[1] if len(sys.argv) > 1 else "arxiv_papers.json"
    
    print("📚 ArXiv Paper Manager - JSON Importer")
    print("=" * 50)
    
    success = load_papers_from_json(json_file)
    
    if not success:
        sys.exit(1)
    
    print("\n✨ Import completed successfully!")

if __name__ == "__main__":
    main()