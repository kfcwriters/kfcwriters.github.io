import json
import os
import sys
import re
from datetime import datetime

def main():
    # Read the DOI from cache
    cache_file = "doi_cache.json"
    if not os.path.exists(cache_file):
        print("No DOI cache found. Run fetch_doi.py first.")
        sys.exit(1)
    with open(cache_file, "r") as f:
        cache = json.load(f)
    doi = list(cache.values())[0]

    # Determine today's article file
    today = datetime.utcnow().strftime("%Y-%m-%d")
    article_file = f"Journal/review-{today}.html"
    if not os.path.exists(article_file):
        print(f"Article file {article_file} not found.")
        sys.exit(1)

    # Read the HTML
    with open(article_file, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace the placeholder with the DOI
    # The placeholder is: <span id="doi-value">will be assigned after publication</span>
    # We'll replace the entire span content
    pattern = r'(<span id="doi-value">)(.*?)(</span>)'
    replacement = rf'\g<1>{doi}\g<3>'
    new_html = re.sub(pattern, replacement, html)

    # Also add a meta tag in the head (for citation)
    meta_doi = f'<meta name="citation_doi" content="{doi}">'
    if 'citation_doi' not in new_html:
        new_html = new_html.replace('</head>', f'{meta_doi}\n</head>')

    # Write back
    with open(article_file, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"Injected DOI {doi} into {article_file}")

if __name__ == "__main__":
    main()
