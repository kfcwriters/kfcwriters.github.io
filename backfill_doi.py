import os
import re
import json
import time
import requests

CONCEPT_RECID = "20559439"
ZENODO_TOKEN = os.environ.get("ZENODO_TOKEN")

# Static fallback for already known DOIs (used only if API fails)
KNOWN_DOIS = {
    "article-2026-06-05": "10.5281/zenodo.20559776",
    "article-2026-06-06": "10.5281/zenodo.20570421",
    "article-2026-06-07": "10.5281/zenodo.20580199",
    # add future known DOIs here if needed
}

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r", encoding="utf-8") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_via_search_api(tag, max_attempts=5, delay=30):
    """Use Zenodo search API with conceptrecid to find DOI for a version tag."""
    if not ZENODO_TOKEN:
        print("ZENODO_TOKEN not set. Skipping API fetch.")
        return None
    headers = {"Authorization": f"Bearer {ZENODO_TOKEN}"}
    # Search for all records belonging to the concept
    url = f"https://zenodo.org/api/records?q=conceptrecid:{CONCEPT_RECID}&size=1000"
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: API returned {resp.status_code}")
                if attempt < max_attempts - 1:
                    time.sleep(delay)
                continue
            data = resp.json()
            # Iterate through all records (paginated if necessary)
            while True:
                for record in data.get("hits", {}).get("hits", []):
                    metadata = record.get("metadata", {})
                    version = metadata.get("version", "")
                    if version == tag:
                        return record["doi"]
                # Next page
                next_link = data.get("links", {}).get("next")
                if not next_link:
                    break
                resp = requests.get(next_link, headers=headers, timeout=30)
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
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    html = re.sub(r'(<span id="doi-value">)(.*?)(</span>)', rf'\g<1>{doi}\g<3>', html)
    if 'citation_doi' not in html:
        html = html.replace('</head>', f'<meta name="citation_doi" content="{doi}">\n</head>')
    with open(path, "w", encoding="utf-8") as f:
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

        # Try static fallback first
        if tag in KNOWN_DOIS:
            doi = KNOWN_DOIS[tag]
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Used static DOI for {tag}")
            continue

        # Use search API with token
        print(f"Fetching DOI for {tag} from Zenodo search API...")
        doi = fetch_doi_via_search_api(tag)
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
