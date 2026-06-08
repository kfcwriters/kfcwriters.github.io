import os
import re
import json
import time
import requests

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_via_search_page(tag, max_attempts=20, delay=30):
    """Scrape DOI from Zenodo search page for a given version tag."""
    search_url = f"https://zenodo.org/search?q=version:{tag}&l=list&p=1&s=10&sort=version"
    for attempt in range(max_attempts):
        try:
            resp = requests.get(search_url, timeout=30)
            if resp.status_code == 200:
                # Look for a DOI pattern (10.5281/zenodo. followed by digits)
                match = re.search(r'10\.5281/zenodo\.\d+', resp.text)
                if match:
                    return match.group(0)
            print(f"Attempt {attempt+1}/{max_attempts}: DOI not yet visible. Status {resp.status_code}.")
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        if attempt < max_attempts - 1:
            print(f"Waiting {delay} seconds...")
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

        print(f"Searching for DOI of {tag} (up to 10 minutes)...")
        doi = fetch_doi_via_search_page(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"❌ DOI for {tag} not found after {20*30//60} minutes. Will retry next hour.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
