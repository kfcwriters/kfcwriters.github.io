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
        with open(os.path.join("Journal", fname), "r") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_by_title(date_str):
    """Search Zenodo using the exact title."""
    title = f"kfcwriters/kfcwriters.github.io: Article {date_str}"
    url = f"https://zenodo.org/api/records?q=title:\"{quote(title)}\"&size=1"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if hits:
                return hits[0]["doi"]
    except:
        pass
    return None

def fetch_doi_by_release_url(tag):
    """Fallback: search by GitHub release URL."""
    release_url = f"https://github.com/kfcwriters/kfcwriters.github.io/releases/tag/{tag}"
    url = f"https://zenodo.org/api/records?q=related_identifier:\"{quote(release_url)}\"&size=1"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if hits:
                return hits[0]["doi"]
    except:
        pass
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
    cache_file = "doi_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)

    for fname in missing:
        match = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not match:
            continue
        date_str = match.group(1)
        tag = f"article-{date_str}"
        if tag in cache:
            inject_doi(fname, cache[tag])
            continue

        # Try exact title search first
        doi = fetch_doi_by_title(date_str)
        if not doi:
            # Fallback to release URL search
            doi = fetch_doi_by_release_url(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"⚠️ DOI for {tag} not yet available. Will retry later.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
