import os
import re
import json
import time
import requests

# Concept record URL (using the conceptrecid, not the DOI)
CONCEPT_RECORD_URL = "https://zenodo.org/record/20559439"

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_from_concept_page(tag, max_attempts=6, delay=30):
    """Scrape the concept record HTML page to find DOI for the given version tag."""
    for attempt in range(max_attempts):
        try:
            resp = requests.get(CONCEPT_RECORD_URL, timeout=30)
            if resp.status_code != 200:
                print(f"Attempt {attempt+1}: Concept page status {resp.status_code}")
                time.sleep(delay)
                continue
            html = resp.text
            # Find all DOI entries and their associated version tags.
            # The page structure: each version block contains a DOI and a version string.
            # We'll search for patterns like: 10.5281/zenodo.xxxxxx ... Version: article-2026-06-07
            # Simpler: locate the version tag, then find the nearest DOI.
            # Use regex to find version tags and then capture DOI in the same block.
            # We'll find all occurrences of "Version: <tag>" and then look for the DOI before it.
            # A more straightforward approach: split the HTML into version sections.
            # But regex is easier for this.
            # Search for pattern: DOI 10.5281/zenodo.\d+ followed anywhere after that a line containing Version: article-...
            # Or search for version tag and then backtrack to the preceding DOI.
            # Since the HTML structure is consistent, we can do:
            # Find all matches of: (10\.5281/zenodo\.\d+).*?Version: {tag}
            pattern = rf'(10\.5281/zenodo\.\d+).*?Version:\s*{re.escape(tag)}'
            match = re.search(pattern, html, re.DOTALL)
            if match:
                return match.group(1)
            # Also try to find the version tag in a <div> and get the DOI from a nearby <span>
            # Fallback: search for version tag then look for DOI in the same table row.
            # We'll use a more generic search: find the line with version, then capture the DOI that appears earlier.
            # Simpler: split by 'Version:' and look at the previous chunk.
            parts = re.split(r'Version:\s*', html)
            for i, part in enumerate(parts):
                if part.startswith(tag):
                    # The DOI is in the previous part (or within the same part)
                    # Find DOI in the previous part
                    doi_match = re.search(r'10\.5281/zenodo\.\d+', parts[i-1])
                    if doi_match:
                        return doi_match.group(0)
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

        print(f"Looking up DOI for {tag} from concept record...")
        doi = fetch_doi_from_concept_page(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"❌ DOI for {tag} not found on concept page. Will retry next hour.")

    with open(cache_file, "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
