import os
import re
import json
import time
import requests

CONCEPT_PAGE_URL = "https://zenodo.org/record/20559439"

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname)) as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_from_concept_page(tag, max_attempts=6, delay=30):
    """Scrape the concept record HTML page to find DOI for the given version tag."""
    for attempt in range(max_attempts):
        try:
            resp = requests.get(CONCEPT_PAGE_URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: page status {resp.status_code}")
                time.sleep(delay)
                continue
            html = resp.text
            # Find the version tag in the page. The page contains many "Version: article-2026-06-07" strings.
            # We need to capture the DOI that precedes it. Look for a pattern: DOI 10.5281/zenodo.xxxxxx and then later Version: tag
            # Use a regex that captures a DOI and then later the version tag within a short window.
            # Simpler: split the page by 'Version:' and look at the chunk before the tag.
            parts = re.split(r'Version:\s*', html)
            for i, part in enumerate(parts):
                if part.startswith(tag):
                    # The DOI is in the previous part (or within the previous 500 chars)
                    # Look for a DOI pattern in the previous part
                    prev = parts[i-1]
                    doi_match = re.search(r'10\.5281/zenodo\.\d+', prev)
                    if doi_match:
                        return doi_match.group(0)
            # Also try a direct search: find all DOI occurrences and then the nearest version tag
            # But the above split method should work.
        except Exception as e:
            print(f"Attempt {attempt+1} error: {e}")
        print(f"Attempt {attempt+1}/{max_attempts}: DOI for {tag} not yet on concept page. Waiting {delay}s...")
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

        print(f"Searching concept page for DOI of {tag}...")
        doi = fetch_doi_from_concept_page(tag)
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
