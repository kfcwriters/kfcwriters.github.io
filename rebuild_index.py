import os, sys, json, base64, requests, logging

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

def build_index(files):
    links = "\n".join([f'<li><a href="{f["name"]}">{f["name"].replace("review-","").replace(".html","")}</a></li>' for f in files])
    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Original Medical Reviews</title>
    <style>
        body {{ font-family: Georgia, serif; max-width: 800px; margin: 40px auto; padding: 0 20px; }}
        h1 {{ color: #0d47a1; }}
        ul {{ list-style: none; padding: 0; }}
        li {{ margin: 10px 0; }}
        a {{ text-decoration: none; color: #0d47a1; }}
    </style>
</head>
<body>
    <h1>Original Medical Reviews</h1>
    <p>Published by the Knowledge Framework Consulting Journal of Medical Writing Reviews.</p>
    <ul>{links}</ul>
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
        "message": "Update review index",
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
