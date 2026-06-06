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

def fetch_doi_for_tag(tag, max_retries=10):
    """Retrieve DOI for a given GitHub release tag using Zenodo API."""
    # Strategy 1: search by version (exact match)
    version_query = f'version:"{tag}"'
    url = f"https://zenodo.org/api/records?q={version_query}&size=1"
    
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                # Handle both "hits" and direct list (old API style)
                records = data.get("hits", {}).get("hits", []) if "hits" in data else data.get("records", [])
                if records:
                    doi = records[0]["doi"]
                    print(f"Found DOI via version: {doi}")
                    return doi
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        
        print(f"Retry {attempt+1}/{max_retries} for {tag}...")
        time.sleep(30)
    
    # Strategy 2: search by related identifier (GitHub release URL)
    release_url = f"https://github.com/kfcwriters/kfcwriters.github.io/releases/tag/{tag}"
    related_query = f'related_identifier:"{release_url}"'
    url = f"https://zenodo.org/api/records?q={related_query}&size=1"
    
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                records = data.get("hits", {}).get("hits", []) if "hits" in data else data.get("records", [])
                if records:
                    doi = records[0]["doi"]
                    print(f"Found DOI via related_identifier: {doi}")
                    return doi
        except Exception:
            pass
        time.sleep(30)
    
    return None

def inject_doi(filename, doi):
    path = os.path.join("Journal", filename)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    # Replace placeholder
    html = re.sub(r'(<span id="doi-value">)(.*?)(</span>)', rf'\g<1>{doi}\g<3>', html)
    # Add meta tag if missing
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

        doi = fetch_doi_for_tag(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
        else:
            print(f"⚠️ DOI for {tag} still not available. Will retry next hour.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
