import os
import re
import json
import requests
import time

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname)) as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_from_zenodo_html(tag):
    """
    Directly fetch the Zenodo record page by searching for the version.
    This is more reliable than the API.
    """
    # Construct a search URL that points to the exact version
    search_url = f"https://zenodo.org/search?q=version:{tag}&l=list&p=1&s=10&sort=version"
    try:
        resp = requests.get(search_url, timeout=30)
        if resp.status_code == 200:
            # Find the DOI pattern in the HTML
            match = re.search(r'10\.5281/zenodo\.\d+', resp.text)
            if match:
                return match.group(0)
    except:
        pass
    return None

def inject_doi(filename, doi):
    path = os.path.join("Journal", filename)
    with open(path) as f:
        html = f.read()
    html = re.sub(r'(<span id="doi-value">)(.*?)(</span>)', rf'\g<1>{doi}\g<3>', html)
    if 'citation_doi' not in html:
        html = html.replace('</head>', f'<meta name="citation_doi" content="{doi}">\n</head>')
    with open(path, 'w') as f:
        f.write(html)
    print(f"Injected {doi} into {filename}")

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

        doi = fetch_doi_from_zenodo_html(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
            print(f"Fetched DOI {doi} for {tag}")
        else:
            print(f"⚠️ DOI for {tag} not found. Will retry later.")

    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
