import os
import re
import json
import time
import requests
from urllib.parse import urljoin

CONCEPT_RECID = "20559439"
ZENODO_TOKEN = os.environ.get("ZENODO_TOKEN")

# If token is missing, print error and exit
if not ZENODO_TOKEN:
    print("ERROR: ZENODO_TOKEN environment variable not set. Please add the secret.")
    exit(1)

HEADERS = {"Authorization": f"Bearer {ZENODO_TOKEN}"}

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname)) as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_from_concept_api(tag, max_attempts=5, delay=30):
    """Fetch DOI by getting concept record and following versions link."""
    # First, get the concept record
    concept_url = f"https://zenodo.org/api/records/{CONCEPT_RECID}"
    for attempt in range(max_attempts):
        try:
            resp = requests.get(concept_url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: Concept record returned {resp.status_code}")
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                continue
            concept = resp.json()
            versions_url = concept["links"]["versions"]
            # Now fetch versions (paginated)
            while versions_url:
                resp = requests.get(versions_url, headers=HEADERS, timeout=30)
                if resp.status_code != 200:
                    break
                data = resp.json()
                for record in data.get("hits", {}).get("hits", []):
                    version = record.get("metadata", {}).get("version", "")
                    if version == tag:
                        return record["doi"]
                versions_url = data.get("links", {}).get("next")
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        if attempt < max_attempts - 1:
            print(f"Retrying in {delay}s...")
            time.sleep(delay)
    return None

def fetch_doi_via_search_api(tag, max_attempts=5, delay=30):
    """Fallback: use search API with conceptrecid."""
    url = f"https://zenodo.org/api/records?q=conceptrecid:{CONCEPT_RECID}&size=1000"
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: Search API returned {resp.status_code}")
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                continue
            data = resp.json()
            # Paginate
            while True:
                for record in data.get("hits", {}).get("hits", []):
                    if record.get("metadata", {}).get("version") == tag:
                        return record["doi"]
                next_link = data.get("links", {}).get("next")
                if not next_link:
                    break
                resp = requests.get(next_link, headers=HEADERS, timeout=30)
                if resp.status_code != 200:
                    break
                data = resp.json()
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        if attempt < max_attempts - 1:
            print(f"Retrying in {delay}s...")
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

    # Load cache
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

        print(f"Searching for DOI for {tag}...")
        doi = fetch_doi_from_concept_api(tag)
        if not doi:
            doi = fetch_doi_via_search_api(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi}")
        else:
            print(f"❌ DOI for {tag} not found after multiple attempts. Will retry next hour.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
