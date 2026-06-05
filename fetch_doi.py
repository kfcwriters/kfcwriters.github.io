import requests
import sys
import json
import os
import time

def main():
    # Get release tag from environment (set by GitHub Actions)
    tag = os.environ.get("RELEASE_TAG")
    if not tag and len(sys.argv) > 1:
        tag = sys.argv[1]
    if not tag:
        print("No release tag provided. Exiting.")
        sys.exit(1)

    # Zenodo API: search for records with this keyword
    url = f"https://zenodo.org/api/records?q=keywords:\"{tag}\""
    for attempt in range(6):  # retry up to 6 times (approx 3 minutes)
        try:
            resp = requests.get(url, timeout=30)
            data = resp.json()
            if data["hits"]["total"] > 0:
                doi = data["hits"]["hits"][0]["doi"]
                print(f"DOI found: {doi}")
                # Save to cache file
                with open("doi_cache.json", "w") as f:
                    json.dump({tag: doi}, f)
                # Set output for GitHub Actions
                with open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a") as f:
                    f.write(f"DOI={doi}\n")
                return
            else:
                print(f"Attempt {attempt+1}/6: DOI not yet assigned. Waiting 30 seconds...")
                time.sleep(30)
        except Exception as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(30)
    print("DOI not found after multiple attempts. Exiting without DOI.")
    sys.exit(1)

if __name__ == "__main__":
    main()
