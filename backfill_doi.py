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

def fetch_doi_from_web(tag):
    """Scrape the DOI from the Zenodo search page for a given version tag."""
    search_url = f"https://zenodo.org/search?q=version:{tag}&l=list&p=1&s=10&sort=version"
    try:
        resp = requests.get(search_url, timeout=30)
        if resp.status_code == 200:
            # Look for a DOI pattern in the HTML
            match = re.search(r'10\.5281/zenodo\.\d+', resp.text)
            if match:
                return match.group(0)
    except Exception as e:
        print(f"Error scraping DOI: {e}")
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

    for fname in missing:
        match = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not match:
            continue
        tag = f"article-{match.group(1)}"
        # Retry up to 12 times (6 minutes) to allow Zenodo to become available
        for attempt in range(12):
            doi = fetch_doi_from_web(tag)
            if doi:
                inject_doi(fname, doi)
                print(f"Fetched DOI {doi} for {tag}")
                break
            else:
                print(f"Attempt {attempt+1}/12: DOI for {tag} not yet visible. Waiting 30s...")
                time.sleep(30)
        else:
            print(f"❌ Could not fetch DOI for {tag} after 12 attempts. Will retry next hour.")

if __name__ == "__main__":
    main()
