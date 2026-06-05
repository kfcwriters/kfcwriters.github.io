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

def fetch_doi_by_title(tag):
    """Search Zenodo by exact title: 'kfcwriters/kfcwriters.github.io: Article YYYY-MM-DD'"""
    date_part = tag.replace("article-", "")  # e.g., 2026-06-05
    title = f"kfcwriters/kfcwriters.github.io: Article {date_part}"
    url = f"https://zenodo.org/api/records?q=title:\"{title}\""
    try:
        resp = requests.get(url, timeout=30)
        data = resp.json()
        if data["hits"]["total"] > 0:
            return data["hits"]["hits"][0]["doi"]
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

    cache = {}
    if os.path.exists("doi_cache.json"):
        with open("doi_cache.json", "r") as f:
            cache = json.load(f)

    for fname in missing:
        match = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not match:
            continue
        tag = f"article-{match.group(1)}"
        if tag in cache:
            inject_doi(fname, cache[tag])
            continue
        doi = fetch_doi_by_title(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
        else:
            print(f"DOI not yet available for {tag}")

    with open("doi_cache.json", "w") as f:
        json.dump(cache, f)

if __name__ == "__main__":
    main()
