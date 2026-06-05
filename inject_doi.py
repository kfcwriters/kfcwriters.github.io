import sys
import json
import os
from bs4 import BeautifulSoup

def main():
    # Get the DOI from the cache file
    cache_file = "doi_cache.json"
    if not os.path.exists(cache_file):
        print("No DOI cache found. Run fetch_doi.py first.")
        sys.exit(1)

    with open(cache_file, "r") as f:
        cache = json.load(f)
    # The latest tag is the first/only key; we can take the first value
    doi = list(cache.values())[0]

    # Determine the article file based on today's date
    date_str = os.environ.get("DATE")
    if not date_str:
        # Try to get from a file or use current UTC date
        import datetime
        date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    article_file = f"Journal/review-{date_str}.html"
    if not os.path.exists(article_file):
        print(f"Article file {article_file} not found.")
        sys.exit(1)

    # Read and modify the HTML
    with open(article_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Add DOI meta tag in head
    meta = soup.new_tag("meta", name="citation_doi", content=doi)
    soup.head.append(meta)

    # Update the visible DOI span
    doi_span = soup.find("span", id="doi-value")
    if doi_span:
        doi_span.string = doi
    else:
        # If not found, try to replace the placeholder text
        doi_div = soup.find("div", class_="doi")
        if doi_div:
            doi_div.string = f"DOI: {doi}"

    with open(article_file, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print(f"Injected DOI {doi} into {article_file}")

if __name__ == "__main__":
    main()
