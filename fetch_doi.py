import requests
import sys
import json
import os
import time

def main():
    tag = os.environ.get("RELEASE_TAG")
    if not tag and len(sys.argv) > 1:
        tag = sys.argv[1]
    if not tag:
        print("No release tag provided.")
        return

    repo = "kfcwriters/kfcwriters.github.io"
    release_url = f"https://github.com/{repo}/releases/tag/{tag}"
    print(f"Searching Zenodo for DOI using release URL: {release_url}")

    for attempt in range(6):
        try:
            search_url = f"https://zenodo.org/api/records?q=related_identifier:\"{release_url}\""
            resp = requests.get(search_url, timeout=30)
            data = resp.json()
            if data["hits"]["total"] > 0:
                doi = data["hits"]["hits"][0]["doi"]
                print(f"DOI found: {doi}")
                with open("doi_cache.json", "w") as f:
                    json.dump({tag: doi}, f)
                with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
                    f.write(f"DOI={doi}\n")
                return
        except Exception as e:
            print(f"Search error: {e}")

        print(f"Attempt {attempt+1}/6: DOI not yet assigned. Waiting 30 seconds...")
        time.sleep(30)

    print("DOI not found after 6 attempts.")
    with open("doi_cache.json", "w") as f:
        json.dump({}, f)

if __name__ == "__main__":
    main()
