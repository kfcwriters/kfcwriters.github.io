import os
import re
import json
import time
import requests

# This is the permanent concept DOI for your repository (obtained once from Zenodo)
CONCEPT_DOI = "10.5281/zenodo.20559439"

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_for_release(tag):
    """Get DOI for a specific version tag using the concept DOI."""
    concept_url = f"https://zenodo.org/api/records/{CONCEPT_DOI}"
    try:
        resp = requests.get(concept_url, timeout=10)
        if resp.status_code != 200:
            return None
        concept = resp.json()
        versions_url = concept["links"]["versions"]
        # Fetch all versions (paginated)
        while versions_url:
            resp = requests.get(versions_url, timeout=10)
            if resp.status_code != 200:
                break
            data = resp.json()
            for record in data.get("hits", {}).get("hits", []):
                metadata = record.get("metadata", {})
                version = metadata.get("version", "")
                if version == tag:
                    return record["doi"]
            versions_url = data.get("links", {}).get("next")
    except Exception as e:
        print(f"Error: {e}")
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
        # Only retry 3 times (30 seconds total) because the concept versions list is immediate
        for attempt in range(3):
            doi = fetch_doi_for_release(tag)
            if doi:
                inject_doi(fname, doi)
                print(f"Fetched DOI {doi} for {tag}")
                break
            else:
                print(f"Attempt {attempt+1}/3: DOI for {tag} not yet in version list. Waiting 10s...")
                time.sleep(10)
        else:
            print(f"❌ Could not fetch DOI for {tag} after 3 attempts. It may appear later.")

if __name__ == "__main__":
    main()
