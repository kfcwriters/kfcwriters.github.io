import os
import re
import json
import time
import requests
from datetime import datetime

# Concept record URL – all versions of your journal are listed here
CONCEPT_PAGE = "https://zenodo.org/record/20559439"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_articles_missing_doi():
    """Return list of article files that still have the placeholder."""
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r", encoding="utf-8") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_from_concept_page(tag, max_attempts=6, delay=30):
    """Scrape the concept page to find DOI for a given version tag."""
    for attempt in range(max_attempts):
        try:
            resp = requests.get(CONCEPT_PAGE, headers=HEADERS, timeout=30)
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: HTTP {resp.status_code}")
                time.sleep(delay)
                continue
            html = resp.text
            # The page contains lines like:
            #   <span class="version">article-2026-06-07</span>
            #   ... nearby there is a DOI link
            # Simpler: split by 'Version:' and look at the preceding block
            parts = re.split(r'Version:\s*', html)
            for i, part in enumerate(parts):
                if part.startswith(tag):
                    # The DOI is in the previous part
                    prev = parts[i-1]
                    doi_match = re.search(r'10\.5281/zenodo\.\d+', prev)
                    if doi_match:
                        return doi_match.group(0)
            # Fallback: search for the tag anywhere and then find the nearest DOI
            match = re.search(rf'(10\.5281/zenodo\.\d+).*?{re.escape(tag)}', html, re.DOTALL)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        print(f"Attempt {attempt+1}/{max_attempts}: DOI for {tag} not yet visible. Waiting {delay}s...")
        time.sleep(delay)
    return None

def inject_doi(filename, doi):
    """Replace placeholder with real DOI and add meta tag."""
    path = os.path.join("Journal", filename)
    with open(path, "r", encoding="utf-8") as f:
        html = f.read()
    # Replace the span content
    html = re.sub(r'(<span id="doi-value">)(.*?)(</span>)', rf'\g<1>{doi}\g<3>', html)
    # Add citation_doi meta tag if missing
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

    # Load existing cache
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

        print(f"Looking up DOI for {tag}...")
        doi = fetch_doi_from_concept_page(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi}")
        else:
            print(f"❌ DOI for {tag} not found. You can manually add it to doi_cache.json: {{\"{tag}\": \"10.5281/zenodo.XXXXXX\"}}")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
