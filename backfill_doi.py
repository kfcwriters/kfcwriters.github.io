import os
import re
import json
import time
import requests
from datetime import datetime

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        path = os.path.join("Journal", fname)
        with open(path, "r", encoding="utf-8") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_via_github_release(tag):
    """Query Zenodo using the GitHub release URL as related_identifier."""
    release_url = f"https://github.com/kfcwriters/kfcwriters.github.io/releases/tag/{tag}"
    url = f"https://zenodo.org/api/records?q=related_identifier:\"{release_url}\"&size=1"
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

def fetch_doi_via_html_search(tag):
    """Fallback: scrape Zenodo's search page for the version."""
    search_url = f"https://zenodo.org/search?q=version:{tag}&l=list&p=1&s=10&sort=version"
    try:
        resp = requests.get(search_url, timeout=30)
        if resp.status_code == 200:
            match = re.search(r'10\.5281/zenodo\.\d+', resp.text)
            if match:
                return match.group(0)
    except:
        pass
    return None

def inject_doi(filename, doi):
    path = os.path.join("Journal", filename)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    html = re.sub(r'(<span id="doi-value">)(.*?)(</span>)', rf'\g<1>{doi}\g<3>', html)
    meta = f'<meta name="citation_doi" content="{doi}">'
    if 'citation_doi' not in html:
        html = html.replace('</head>', f'{meta}\n</head>')
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Injected DOI {doi} into {filename}")

def main():
    missing = get_articles_missing_doi()
    if not missing:
        print("No articles missing DOI.")
        return

    # Hardcoded known DOI for the problematic release (only needed once)
    known_missing = {
        "article-2026-06-06": "10.5281/zenodo.20570421"
    }

    cache = {}
    cache_file = "doi_cache.json"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            cache = json.load(f)

    for fname in missing:
        match = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not match:
            continue
        tag = f"article-{match.group(1)}"
        if tag in cache:
            inject_doi(fname, cache[tag])
            continue

        # First try the hardcoded map (for the known problematic release)
        if tag in known_missing:
            doi = known_missing[tag]
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Used hardcoded DOI for {tag}")
            continue

        # Otherwise attempt live fetch
        doi = fetch_doi_via_github_release(tag)
        if not doi:
            doi = fetch_doi_via_html_search(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"⚠️ DOI for {tag} not found. Will retry next hour.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
