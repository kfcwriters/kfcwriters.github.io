import os
import re
import json
import requests

CONCEPT_RECID = "20559439"
ZENODO_TOKEN = os.environ.get("ZENODO_TOKEN")

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname)) as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_via_api(tag):
    if not ZENODO_TOKEN:
        print("ZENODO_TOKEN not set. Cannot fetch DOIs automatically.")
        return None
    headers = {"Authorization": f"Bearer {ZENODO_TOKEN}"}
    url = f"https://zenodo.org/api/records?q=conceptrecid:{CONCEPT_RECID}&size=1000"
    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code != 200:
            print(f"API error: {resp.status_code}")
            return None
        data = resp.json()
        for record in data.get("hits", {}).get("hits", []):
            metadata = record.get("metadata", {})
            if metadata.get("version") == tag:
                return record["doi"]
        # Paginate if needed
        next_link = data.get("links", {}).get("next")
        while next_link:
            resp = requests.get(next_link, headers=headers, timeout=30)
            if resp.status_code != 200:
                break
            data = resp.json()
            for record in data.get("hits", {}).get("hits", []):
                metadata = record.get("metadata", {})
                if metadata.get("version") == tag:
                    return record["doi"]
            next_link = data.get("links", {}).get("next")
    except Exception as e:
        print(f"API exception: {e}")
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
        doi = fetch_doi_via_api(tag)
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
