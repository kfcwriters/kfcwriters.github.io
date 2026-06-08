import os
import re
import json
import time
import requests

CONCEPT_RECID = "20559439"  # from concept DOI 10.5281/zenodo.20559439
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ZenodoBackfill/1.0)"}
MAX_ATTEMPTS = 6
RETRY_DELAY = 30

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
    """Fetch DOI for a version tag using conceptrecid search."""
    url = f"https://zenodo.org/api/records?q=conceptrecid:{CONCEPT_RECID}&size=1000"
    for attempt in range(MAX_ATTEMPTS):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: API status {resp.status_code}")
                time.sleep(RETRY_DELAY)
                continue
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            for record in hits:
                metadata = record.get("metadata", {})
                version = metadata.get("version", "")
                if version == tag:
                    return record["doi"]
            # If not found in first page, there may be pagination, but the query with size=1000 should get all.
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        print(f"Attempt {attempt+1}/{MAX_ATTEMPTS}: DOI for {tag} not yet in list. Waiting {RETRY_DELAY}s...")
        time.sleep(RETRY_DELAY)
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

        print(f"Searching for DOI of {tag} (up to {MAX_ATTEMPTS*RETRY_DELAY//60} minutes)...")
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
