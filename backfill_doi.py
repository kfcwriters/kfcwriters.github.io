import os
import re
import json
import requests
from datetime import datetime

CONCEPT_RECID = "20559439"  # Your concept record ID
ZENODO_TOKEN = os.environ.get("ZENODO_TOKEN")

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname)) as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_for_tag(tag):
    """Use Zenodo API with token to list all versions of the concept."""
    if not ZENODO_TOKEN:
        print("ZENODO_TOKEN not set. Please add it as a GitHub secret.")
        return None
    headers = {"Authorization": f"Bearer {ZENODO_TOKEN}"}
    # Get all versions of the concept
    url = f"https://zenodo.org/api/records/{CONCEPT_RECID}/versions?access_token={ZENODO_TOKEN}"
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"API error: {resp.status_code}")
            return None
        data = resp.json()
        for record in data.get("hits", {}).get("hits", []):
            metadata = record.get("metadata", {})
            version = metadata.get("version", "")
            if version == tag:
                return record["doi"]
        # Pagination if needed
        while "next" in data.get("links", {}):
            next_url = data["links"]["next"]
            resp = requests.get(next_url, headers=headers, timeout=30)
            if resp.status_code != 200:
                break
            data = resp.json()
            for record in data.get("hits", {}).get("hits", []):
                metadata = record.get("metadata", {})
                version = metadata.get("version", "")
                if version == tag:
                    return record["doi"]
    except Exception as e:
        print(f"Error: {e}")
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
        with open(cache_file) as f:
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
            print(f"Fetched DOI {doi}")
        else:
            print(f"❌ DOI for {tag} not found. Will retry next hour.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
