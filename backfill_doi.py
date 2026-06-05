import os
import re
import json
import requests
import time
from datetime import datetime

def get_articles_missing_doi():
    """Return list of article files that still have placeholder DOI."""
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        path = os.path.join("Journal", fname)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if 'will be assigned after publication' in content:
            missing.append(fname)
    return missing

def fetch_doi_for_release(tag):
    """Search Zenodo using GitHub release URL."""
    repo = "kfcwriters/kfcwriters.github.io"
    release_url = f"https://github.com/{repo}/releases/tag/{tag}"
    search_url = f"https://zenodo.org/api/records?q=related_identifier:\"{release_url}\""
    try:
        resp = requests.get(search_url, timeout=30)
        data = resp.json()
        if data["hits"]["total"] > 0:
            return data["hits"]["hits"][0]["doi"]
    except:
        pass
    return None

def inject_doi_into_article(filename, doi):
    path = os.path.join("Journal", filename)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    pattern = r'(<span id="doi-value">)(.*?)(</span>)'
    new_html = re.sub(pattern, rf'\g<1>{doi}\g<3>', html)
    meta_doi = f'<meta name="citation_doi" content="{doi}">'
    if 'citation_doi' not in new_html:
        new_html = new_html.replace('</head>', f'{meta_doi}\n</head>')
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"Injected DOI {doi} into {filename}")

def main():
    missing = get_articles_missing_doi()
    if not missing:
        print("No articles missing DOI.")
        return
    # Load existing DOI cache
    cache = {}
    if os.path.exists("doi_cache.json"):
        with open("doi_cache.json", "r") as f:
            cache = json.load(f)
    for fname in missing:
        # Extract tag from filename: review-2026-06-05.html -> article-2026-06-05
        match = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not match:
            continue
        tag = f"article-{match.group(1)}"
        if tag in cache:
            doi = cache[tag]
            inject_doi_into_article(fname, doi)
            continue
        doi = fetch_doi_for_release(tag)
        if doi:
            cache[tag] = doi
            inject_doi_into_article(fname, doi)
        else:
            print(f"DOI not yet available for {tag}")
    # Save updated cache
    with open("doi_cache.json", "w") as f:
        json.dump(cache, f)

if __name__ == "__main__":
    main()
