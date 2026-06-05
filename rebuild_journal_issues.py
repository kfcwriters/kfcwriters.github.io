import os
import re
import datetime
import base64
import requests
from collections import defaultdict
from pathlib import Path

# Configuration
REPO = "kfcwriters/kfcwriters.github.io"
BRANCH = "main"
JOURNAL_FOLDER = "Journal"
TOKEN = os.environ["WEBSITE_REPO_TOKEN"]
API_BASE = "https://api.github.com"

def get_all_articles():
    """Get list of all review-*.html files from Journal/ folder via GitHub API"""
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    url = f"{API_BASE}/repos/{REPO}/contents/{JOURNAL_FOLDER}"
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        raise Exception(f"Failed to list files: {resp.status_code}")
    files = [item["name"] for item in resp.json() if item["name"].startswith("review-") and item["name"].endswith(".html")]
    return files

def extract_date_from_filename(filename):
    """Extract YYYY-MM-DD from review-2026-06-04.html"""
    match = re.search(r'review-(\d{4}-\d{2}-\d{2})', filename)
    if match:
        return match.group(1)
    return None

def generate_issue_page(volume, issue, articles, year, month):
    """Create HTML for a specific issue (e.g., Journal/volume-1/issue-6/index.html)"""
    # Build list of article cards (similar to main journal index)
    cards_html = ""
    for article in sorted(articles):  # articles are filenames
        # Extract title from the article file content (requires fetching each file - could be slow)
        # For simplicity, we use the filename as placeholder; better to parse the <title> from each file.
        # We'll fetch the content of each article to get the real title.
        # But to keep this example compact, I'll assume we have a way to get titles.
        # In production, you'd fetch each file's content and extract <title>.
        # I'll implement a simple fetch.
        title = get_article_title(article)
        cards_html += f"""
        <div class="article-card">
            <h3><a href="{article}">{title}</a></h3>
            <div class="meta">Published: {extract_date_from_filename(article)}</div>
        </div>"""
    
    # Use the same attractive template as your journal (reuse existing CSS)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Volume {volume}, Issue {issue} – Global Journal of Medical Research</title>
    <style>
        /* Copy the exact same CSS from your current Journal/index.html (the attractive version) */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f4f8; color: #1e2a3a; line-height: 1.5; }}
        .navbar {{ background: #0d47a1; padding: 15px 20px; text-align: center; }}
        .navbar a {{ color: white; text-decoration: none; margin: 0 15px; font-weight: 500; }}
        .journal-header {{ background: linear-gradient(135deg, #0a2b4e, #1e4a76); color: white; text-align: center; padding: 50px 20px; }}
        .journal-header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .container {{ max-width: 1100px; margin: 30px auto; padding: 0 20px; display: flex; flex-wrap: wrap; gap: 30px; }}
        .main {{ flex: 3; background: white; border-radius: 16px; padding: 35px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        .sidebar {{ flex: 1; background: white; border-radius: 16px; padding: 25px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); align-self: start; }}
        .sidebar h3 {{ background: #0d47a1; color: white; padding: 10px; margin: -25px -25px 20px -25px; border-radius: 16px 16px 0 0; }}
        .article-card {{ margin-bottom: 20px; border-bottom: 1px solid #e2e8f0; padding-bottom: 15px; }}
        .article-card h3 a {{ color: #0d47a1; text-decoration: none; }}
        .footer {{ background: #0f2a38; color: #8aaec0; text-align: center; padding: 20px; margin-top: 30px; }}
        .footer a {{ color: #ffaa33; }}
    </style>
</head>
<body>
    <div class="navbar">
        <a href="../index.html">Home</a>
        <a href="../../index.html">Journal Home</a>
        <a href="../../aims-scope.html">Aims & Scope</a>
        <a href="../../editorial-board.html">Editorial Board</a>
        <a href="../../author-guidelines.html">Author Guidelines</a>
        <a href="../../submit.html">Submit Article</a>
    </div>
    <div class="journal-header">
        <h1>Global Journal of Medical Research</h1>
        <p>Volume {volume}, Issue {issue} – {year}</p>
    </div>
    <div class="container">
        <div class="main">
            <h2>Articles in this Issue</h2>
            {cards_html}
        </div>
        <div class="sidebar">
            <h3>Journal Information</h3>
            <p>Co-Chief Editors: Abhishek Bansal & Dr. Praveen Parshant</p>
            <p>Email: kfcwriters@gmail.com</p>
            <a href="../../index.html">Back to Home</a>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Knowledge Framework Consulting</p>
    </div>
</body>
</html>"""

def get_article_title(filename):
    """Fetch the article file from GitHub and extract <title> text"""
    headers = {"Authorization": f"token {TOKEN}"}
    url = f"{API_BASE}/repos/{REPO}/contents/{JOURNAL_FOLDER}/{filename}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        content = base64.b64decode(resp.json()["content"]).decode()
        match = re.search(r"<title>(.*?)</title>", content, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return filename.replace("review-", "").replace(".html", "")

def upload_file(path, content):
    headers = {"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github.v3+json"}
    # Get existing file sha if any
    get_url = f"{API_BASE}/repos/{REPO}/contents/{path}"
    get_resp = requests.get(get_url, headers=headers)
    sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
    data = {
        "message": f"Auto-generate issue page {path}",
        "content": base64.b64encode(content.encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        data["sha"] = sha
    put_url = f"{API_BASE}/repos/{REPO}/contents/{path}"
    put_resp = requests.put(put_url, headers=headers, json=data)
    if put_resp.status_code not in (200, 201):
        raise Exception(f"Failed to upload {path}: {put_resp.text}")

def update_main_index(volumes):
    """Regenerate Journal/index.html to show list of volumes and issues"""
    # Build HTML for volume/issue listing
    listing_html = "<ul>"
    for vol, issues in sorted(volumes.items(), reverse=True):
        listing_html += f"<li><strong>Volume {vol}</strong><ul>"
        for issue_num, articles in sorted(issues.items(), reverse=True):
            # Determine month name from issue number (1-12)
            month_name = datetime.date(2000, issue_num, 1).strftime("%B")
            listing_html += f'<li><a href="volume-{vol}/issue-{issue_num}/index.html">{month_name} {vol} (Issue {issue_num})</a> – {len(articles)} articles</li>'
        listing_html += "</ul></li>"
    listing_html += "</ul>"
    
    # Use the same attractive template with a different main content
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Global Journal of Medical Research</title>
    <style>
        /* same CSS as before */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f4f8; color: #1e2a3a; }}
        .navbar {{ background: #0d47a1; padding: 15px; text-align: center; }}
        .navbar a {{ color: white; margin: 0 15px; text-decoration: none; }}
        .journal-header {{ background: linear-gradient(135deg, #0a2b4e, #1e4a76); color: white; text-align: center; padding: 50px; }}
        .container {{ max-width: 1100px; margin: 30px auto; padding: 0 20px; display: flex; }}
        .main {{ background: white; border-radius: 16px; padding: 30px; flex: 3; }}
        .sidebar {{ background: white; border-radius: 16px; padding: 20px; margin-left: 30px; flex: 1; }}
        .footer {{ background: #0f2a38; color: #ccc; text-align: center; padding: 20px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="navbar">
        <a href="index.html">Home</a>
        <a href="aims-scope.html">Aims & Scope</a>
        <a href="editorial-board.html">Editorial Board</a>
        <a href="author-guidelines.html">Author Guidelines</a>
        <a href="submit.html">Submit Article</a>
    </div>
    <div class="journal-header">
        <h1>Global Journal of Medical Research</h1>
        <p>Open Access | ISSN: Applied for</p>
    </div>
    <div class="container">
        <div class="main">
            <h2>Volumes & Issues</h2>
            {listing_html}
        </div>
        <div class="sidebar">
            <h3>Contact</h3>
            <p>Co-Chief Editors: Abhishek Bansal & Dr. Praveen Parshant</p>
            <p>Email: kfcwriters@gmail.com</p>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Knowledge Framework Consulting</p>
    </div>
</body>
</html>"""
    upload_file(f"{JOURNAL_FOLDER}/index.html", index_html)

def main():
    files = get_all_articles()
    # Group by year (volume) and month (issue)
    groups = defaultdict(lambda: defaultdict(list))
    for filename in files:
        date_str = extract_date_from_filename(filename)
        if not date_str:
            continue
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        volume = dt.year
        issue = dt.month
        groups[volume][issue].append(filename)
    
    # For each volume and issue, generate a page
    for volume, issues in groups.items():
        for issue, articles in issues.items():
            # Create folder path: volume-{volume}/issue-{issue}/
            folder_path = f"{JOURNAL_FOLDER}/volume-{volume}/issue-{issue}"
            # Create the directory (GitHub doesn't support empty folders; we'll create index.html there)
            page_content = generate_issue_page(volume, issue, articles, volume, issue)
            upload_file(f"{folder_path}/index.html", page_content)
    
    # Update main index
    update_main_index(groups)

if __name__ == "__main__":
    main()
