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

def fetch_doi_by_tag(tag):
    """
    Fetch DOI for a given release tag by querying Zenodo for all records
    belonging to the GitHub repository, then matching by version tag.
    """
    # First, get all records for the GitHub repository
    repo_name = "kfcwriters/kfcwriters.github.io"
    # Search for records where the title contains the repo name
    url = f"https://zenodo.org/api/records?q=title:\"{repo_name}\"&size=100"
    try:
        resp = requests.get(url, timeout=30)
        data = resp.json()
        if data["hits"]["total"] > 0:
            for record in data["hits"]["hits"]:
                metadata = record.get("metadata", {})
                # Check the version field (should match tag like "article-2026-06-06")
                version = metadata.get("version", "")
                if version == tag:
                    return record["doi"]
                # Also check related identifiers for GitHub release URL
                related = metadata.get("related_identifiers", [])
                for rel in related:
                    if rel.get("identifier", "").endswith(f"/releases/tag/{tag}"):
                        return record["doi"]
    except Exception as e:
        print(f"Error searching Zenodo: {e}")
    
    # If not found, try pagination
    page = 1
    while True:
        url = f"https://zenodo.org/api/records?q=title:\"{repo_name}\"&size=100&page={page}"
        try:
            resp = requests.get(url, timeout=30)
            data = resp.json()
            if not data["hits"]["hits"]:
                break
            for record in data["hits"]["hits"]:
                metadata = record.get("metadata", {})
                version = metadata.get("version", "")
                if version == tag:
                    return record["doi"]
                related = metadata.get("related_identifiers", [])
                for rel in related:
                    if rel.get("identifier", "").endswith(f"/releases/tag/{tag}"):
                        return record["doi"]
            page += 1
        except:
            break
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
        doi = fetch_doi_by_tag(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"DOI not found for {tag}. You can manually add it to doi_cache.json: \"{tag}\": \"...\"")

    with open("doi_cache.json", "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
