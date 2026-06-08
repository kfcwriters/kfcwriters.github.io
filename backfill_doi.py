import os
import re
import json
import time
import requests

CONCEPT_RECID = "20559439"  # from your concept DOI 10.5281/zenodo.20559439
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ZenodoBackfill/1.0)"}

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_for_tag(tag, max_attempts=6, delay=30):
    """Fetch DOI for a version tag from Zenodo's versions API."""
    url = f"https://zenodo.org/api/records/{CONCEPT_RECID}/versions"
    for attempt in range(max_attempts):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: API status {resp.status_code}")
                time.sleep(delay)
                continue
            data = resp.json()
            # The response contains a 'hits' object with an array of records
            for record in data.get("hits", {}).get("hits", []):
                metadata = record.get("metadata", {})
                version = metadata.get("version", "")
                if version == tag:
                    return record["doi"]
            # If not found, there might be pagination; but the API typically returns all.
            # However, we'll also check the next page if present.
            next_link = data.get("links", {}).get("next")
            while next_link:
                resp = requests.get(next_link, headers=HEADERS, timeout=30)
                if resp.status_code != 200:
                    break
                data = resp.json()
                for record in data.get("hits", {}).get("hits", []):
                    metadata = record.get("metadata", {})
                    version = metadata.get("version", "")
                    if version == tag:
                        return record["doi"]
                next_link = data.get("links", {}).get("next")
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        print(f"Attempt {attempt+1}/{max_attempts}: DOI for {tag} not yet in version list. Waiting {delay}s...")
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

        print(f"Fetching DOI for {tag} from Zenodo versions API...")
        doi = fetch_doi_for_tag(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"❌ DOI for {tag} not found after {max_attempts*delay//60} minutes. Will retry next hour.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
