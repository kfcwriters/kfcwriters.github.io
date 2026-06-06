import os
import re
import json
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

def fetch_doi_from_zenodo(tag):
    """
    Fetch DOI using the GitHub release URL as related_identifier.
    This is the most reliable method.
    """
    release_url = f"https://github.com/kfcwriters/kfcwriters.github.io/releases/tag/{tag}"
    url = f"https://zenodo.org/api/records?q=related_identifier:\"{release_url}\""
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        # Check if 'hits' exists and has items
        if data.get("hits", {}).get("total", 0) > 0:
            return data["hits"]["hits"][0]["doi"]
    except Exception as e:
        print(f"Error in fetch_doi_from_zenodo: {e}")
    return None

def fetch_doi_by_version(tag):
    """
    Search by version string.
    """
    url = f"https://zenodo.org/api/records?q=version:\"{tag}\""
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("hits", {}).get("total", 0) > 0:
            return data["hits"]["hits"][0]["doi"]
    except Exception as e:
        print(f"Error in fetch_doi_by_version: {e}")
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

    # Load existing cache
    cache = {}
    if os.path.exists("doi_cache.json"):
        with open("doi_cache.json", "r") as f:
            cache = json.load(f)

    for fname in missing:
        match = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not match:
            continue
        tag = f"article-{match.group(1)}"
        
        # Check cache first
        if tag in cache:
            inject_doi(fname, cache[tag])
            continue
        
        # Try to fetch DOI
        doi = fetch_doi_from_zenodo(tag) or fetch_doi_by_version(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"DOI not found for {tag}. You can manually add it to doi_cache.json: \"{tag}\": \"...\"")

    # Save updated cache
    with open("doi_cache.json", "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
