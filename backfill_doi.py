import os, re, json, requests, time

def get_articles_missing_doi():
    missing = []
    for fname in os.listdir("Journal"):
        if not fname.startswith("review-") or not fname.endswith(".html"):
            continue
        with open(os.path.join("Journal", fname), "r") as f:
            if 'will be assigned after publication' in f.read():
                missing.append(fname)
    return missing

def fetch_doi_from_github_release(tag):
    release_url = f"https://github.com/kfcwriters/kfcwriters.github.io/releases/tag/{tag}"
    query = f'related_identifier:"{release_url}"'
    url = f"https://zenodo.org/api/records?q={query}&size=1"
    for attempt in range(6):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                data = r.json()
                if data.get("hits", {}).get("total", 0) > 0:
                    return data["hits"]["hits"][0]["doi"]
        except:
            pass
        time.sleep(20)
    return None

def inject_doi(fname, doi):
    path = os.path.join("Journal", fname)
    with open(path, "r") as f:
        html = f.read()
    html = re.sub(r'(<span id="doi-value">)(.*?)(</span>)', rf'\g<1>{doi}\g<3>', html)
    if 'citation_doi' not in html:
        html = html.replace('</head>', f'<meta name="citation_doi" content="{doi}">\n</head>')
    with open(path, "w") as f:
        f.write(html)
    print(f"Injected {doi} into {fname}")

def main():
    missing = get_articles_missing_doi()
    if not missing:
        print("No missing DOIs.")
        return
    cache = {}
    if os.path.exists("doi_cache.json"):
        with open("doi_cache.json") as f:
            cache = json.load(f)
    for fname in missing:
        m = re.search(r'review-(\d{4}-\d{2}-\d{2})', fname)
        if not m:
            continue
        tag = f"article-{m.group(1)}"
        if tag in cache:
            inject_doi(fname, cache[tag])
            continue
        doi = fetch_doi_from_github_release(tag)
        if doi:
            cache[tag] = doi
            inject_doi(fname, doi)
        else:
            print(f"⚠️ Could not fetch DOI for {tag}. Will retry later.")
    with open("doi_cache.json", "w") as f:
        json.dump(cache, f, indent=2)

if __name__ == "__main__":
    main()
