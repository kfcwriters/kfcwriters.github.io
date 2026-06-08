import os
import re
import json
import time
import requests

# Use a known release tag to bootstrap the concept DOI
KNOWN_TAG = "article-2026-06-06"

def get_concept_doi_from_known_tag(tag):
    """Fetch the concept DOI by retrieving the record for a known release."""
    # First, find the record for the known tag by searching by version
    url = f"https://zenodo.org/api/records?q=version:\"{tag}\"&size=1"
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            hits = data.get("hits", {}).get("hits", [])
            if hits:
                record = hits[0]
                # The concept DOI is in the 'conceptdoi' field or 'conceptrecid'
                if "conceptdoi" in record:
                    return record["conceptdoi"]
                # Alternative: construct from conceptrecid
                if "conceptrecid" in record:
                    return f"10.5281/zenodo.{record['conceptrecid']}"
    except Exception as e:
        print(f"Error fetching concept DOI from known tag: {e}")
    return None

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_for_release(tag, concept_doi):
    """Fetch the DOI for a given release tag by listing versions of the concept."""
    concept_url = f"https://zenodo.org/api/records/{concept_doi}"
    try:
        resp = requests.get(concept_url, timeout=30)
        if resp.status_code != 200:
            return None
        concept = resp.json()
        versions_url = concept["links"]["versions"]
        while versions_url:
            resp = requests.get(versions_url, timeout=30)
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
        print(f"Error fetching versions: {e}")
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
    # Get concept DOI from known release
    concept_doi = get_concept_doi_from_known_tag(KNOWN_TAG)
    if not concept_doi:
        print(f"Could not find concept DOI using known tag '{KNOWN_TAG}'. Please check the tag or network.")
        return
    print(f"Using concept DOI: {concept_doi}")

    missing = get_articles_missing_doi()
    if not missing:
        print("No missing DOIs.")
        return

    for fname in missing:
        match = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not match:
            continue
        tag = f"article-{match.group(1)}"
        # Retry up to 12 times (6 minutes) to allow Zenodo to process
        for attempt in range(12):
            doi = fetch_doi_for_release(tag, concept_doi)
            if doi:
                inject_doi(fname, doi)
                print(f"Fetched DOI {doi} for {tag}")
                break
            else:
                print(f"Attempt {attempt+1}/12: DOI for {tag} not yet available. Waiting 30s...")
                time.sleep(30)
        else:
            print(f"❌ Could not fetch DOI for {tag} after 12 attempts. Will retry next hour.")

if __name__ == "__main__":
    main()
