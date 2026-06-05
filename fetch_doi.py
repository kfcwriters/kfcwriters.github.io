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
        print("No release tag provided. Exiting without error.")
        return

    # Try to find DOI using different search strategies
    strategies = [
        f"keywords:\"{tag}\"",
        f"title:\"{tag}\"",
        f"description:\"{tag}\""
    ]
    
    for attempt in range(8):  # ~4 minutes total
        for strategy in strategies:
            url = f"https://zenodo.org/api/records?q={strategy}"
            try:
                resp = requests.get(url, timeout=30)
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
        
        print(f"Attempt {attempt+1}/8: DOI not yet assigned. Waiting 30 seconds...")
        time.sleep(30)
    
    print("DOI not found after multiple attempts. Workflow will continue without DOI.")
    # Create an empty cache file to avoid breaking later steps
    with open("doi_cache.json", "w") as f:
        json.dump({}, f)

if __name__ == "__main__":
    main()
