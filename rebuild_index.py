import os, sys, json, base64, requests, logging, re

logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                    format='%(asctime)s - %(levelname)s - %(message)s')

TOKEN = os.environ["GITHUB_TOKEN"]
REPO = "kfcwriters/kfcwriters.github.io"
BRANCH = "main"
API = "https://api.github.com"
REVIEWS_DIR = "reviews"

def github_get(url):
    headers = {"Authorization": f"token {TOKEN}"}
    return requests.get(url, headers=headers)

def github_put(url, data):
    headers = {"Authorization": f"token {TOKEN}"}
    return requests.put(url, headers=headers, json=data)

def get_files():
    url = f"{API}/repos/{REPO}/contents/{REVIEWS_DIR}"
    resp = github_get(url)
    if resp.status_code == 200:
        return [f for f in resp.json() if f["name"].endswith(".html") and f["name"] != "index.html"]
    return []

def extract_title(download_url):
    try:
        resp = requests.get(download_url, timeout=15)
        if resp.status_code == 200:
            match = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return None

def extract_meta(download_url):
    try:
        resp = requests.get(download_url, timeout=15)
        if resp.status_code == 200:
            match = re.search(r'<p class="meta">.*?<strong>Published:</strong>\s*([^|]+)', resp.text)
            if match:
                return match.group(1).strip()
    except Exception:
        pass
    return ""

def build_index(files):
    cards = []
    for f in files:
        title = extract_title(f["download_url"])
        if not title:
            title = f["name"].replace("review-", "").replace(".html", "")
        date_str = extract_meta(f["download_url"])
        cards.append(f"""
        <div class="article-card">
            <h3><a href="{f['name']}">{title}</a></h3>
            <div class="date">{date_str}</div>
        </div>""")

    cards_html = "\n".join(cards)
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Global Journal of Medical Research</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif; background: #f8fafc; color: #1e293b; }}
        .journal-header {{ background: linear-gradient(135deg, #1e3a5f, #0d47a1); color: white; padding: 50px 20px 40px; text-align: center; }}
        .journal-header h1 {{ font-size: 2.5em; font-weight: 700; margin-bottom: 10px; letter-spacing: -0.5px; }}
        .journal-header .subtitle {{ font-size: 1.1em; opacity: 0.9; font-style: italic; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 30px 20px; }}
        .issn-badge {{ text-align: center; margin-bottom: 30px; color: #64748b; font-size: 0.9em; }}
        .article-card {{ background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); padding: 25px; margin-bottom: 16px; border: 1px solid #e2e8f0; transition: box-shadow 0.2s; }}
        .article-card:hover {{ box-shadow: 0 6px 20px rgba(0,0,0,0.1); }}
        .article-card h3 {{ margin-bottom: 8px; font-size: 1.2em; }}
        .article-card h3 a {{ color: #0d47a1; text-decoration: none; }}
        .article-card h3 a:hover {{ text-decoration: underline; }}
        .article-card .date {{ color: #64748b; font-size: 0.9em; }}
        .contact-info {{ background: white; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); padding: 25px; margin-top: 30px; border: 1px solid #e2e8f0; }}
        .contact-info h2 {{ color: #0d47a1; margin-bottom: 15px; }}
        .contact-info p {{ margin-bottom: 8px; }}
        .footer {{ text-align: center; padding: 30px 20px; color: #64748b; font-size: 0.85em; border-top: 1px solid #e2e8f0; margin-top: 40px; }}
        .footer a {{ color: #0d47a1; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="journal-header">
        <h1>Global Journal of Medical Research</h1>
        <p class="subtitle">Published by Knowledge Framework Consulting</p>
    </div>
    <div class="container">
        <div class="issn-badge">ISSN: Coming soon</div>
        {cards_html}
        <div class="contact-info">
            <h2>Contact Information</h2>
            <p><strong>Publisher:</strong> Knowledge Framework Consulting</p>
            <p><strong>Editor-in-Chief:</strong> Abhishek Bansal</p>
            <p><strong>Email:</strong> kfcwriters@gmail.com</p>
            <p><strong>Phone:</strong> +91 9812018036</p>
            <p><strong>Address:</strong> [Please provide your address – can be city/state or office address]</p>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Knowledge Framework Consulting. All rights reserved.</p>
        <p><a href="https://kfcwriters.github.io">Visit our main site</a> | <a href="mailto:kfcwriters@gmail.com">Contact</a></p>
    </div>
</body>
</html>"""
    return index_html

def upload_index(html_content):
    url = f"{API}/repos/{REPO}/contents/{REVIEWS_DIR}/index.html"
    resp = github_get(url)
    sha = None
    if resp.status_code == 200:
        sha = resp.json()["sha"]
    payload = {
        "message": "Update review index with contact details",
        "content": base64.b64encode(html_content.encode()).decode(),
        "branch": BRANCH
    }
    if sha:
        payload["sha"] = sha
    resp = github_put(url, payload)
    if resp.status_code in (201, 200):
        logging.info("Index page updated.")
    else:
        logging.error(f"Failed to update index: {resp.text}")

def main():
    files = get_files()
    if files:
        html = build_index(files)
        upload_index(html)
    logging.info("Done.")

if __name__ == "__main__":
    main()
