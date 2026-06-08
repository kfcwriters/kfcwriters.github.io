import os
import re
import json
import time
import requests
from urllib.parse import quote

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname)) as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_from_github_release(tag, max_attempts=12, delay=30):
    """Query Zenodo using the GitHub release URL."""
    release_url = f"https://github.com/kfcwriters/kfcwriters.github.io/releases/tag/{tag}"
    # URL‑encode the release URL
    encoded = quote(release_url, safe='')
    api_url = f"https://zenodo.org/api/records?q=related_identifier:\"{encoded}\"&size=1"
    print(f"Query URL: {api_url}")  # for debugging
    for attempt in range(max_attempts):
        try:
            resp = requests.get(api_url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])
                if hits:
                    return hits[0]["doi"]
            else:
                print(f"API returned status {resp.status_code}")
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        print(f"Attempt {attempt+1}/{max_attempts}: DOI not yet available. Waiting {delay}s...")
        time.sleep(delay)
    return None

def inject_doi(filename, doi):
    path = os.path.join("Journal", filename)
    with open(path, "r") as f:
        html = f.read()
    html = re.sub(r'(<span id="doi-value">)(.*?)(</span>)', rf'\g<1>{doi}\g<3>', html)
    if 'citation_doi' not in html:
        html = html.replace('</head>', f'<meta name="citation_doi" content="{doi}">\n</head>')
    with open(path, "w") as f:
        f.write(html)
    print(f"Injected DOI {doi} into {filename}")

def main():
    missing = get_articles_missing_doi()
    if not missing:
        print("No missing DOIs.")
        return

    cache = {}
    if os.path.exists("doi_cache.json"):
        with open("doi_cache.json") as f:
            cache = json.load(f)

    for fname in missing:
        m = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not m:
            continue
        tag = f"article-{m.group(1)}"
        if tag in cache:
            inject_doi(fname, cache[tag])
            continue

        print(f"Waiting for DOI of {tag}...")
        doi = fetch_doi_from_github_release(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi}")
        else:
            print(f"❌ DOI for {tag} not found. Will retry later.")

    with open("doi_cache.json", "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
