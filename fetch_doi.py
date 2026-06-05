import requests
import sys
import json
import os

def main():
    # The tag is passed as an argument from the workflow
    if len(sys.argv) > 1:
        tag = sys.argv[1]
    else:
        tag = os.environ.get("RELEASE_TAG")
        if not tag:
            print("No tag provided. Exiting.")
            sys.exit(1)

    repo = "kfcwriters/kfcwriters.github.io"
    # Search Zenodo for records related to this GitHub release
    url = f"https://zenodo.org/api/records?q=keywords:\"{tag}\""
    try:
        resp = requests.get(url, timeout=30)
        data = resp.json()
        if data["hits"]["total"] > 0:
            doi = data["hits"]["hits"][0]["doi"]
            print(f"DOI found: {doi}")
            # Save DOI to a file for later injection
            with open("doi_cache.json", "w") as f:
                json.dump({tag: doi}, f)
            # Also set an output for GitHub Actions
            with open(os.environ.get('GITHUB_OUTPUT', '/dev/null'), 'a') as f:
                f.write(f"DOI={doi}\n")
        else:
            print("DOI not yet assigned. Zenodo may still be processing.")
            sys.exit(1)
    except Exception as e:
        print(f"Error fetching DOI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
