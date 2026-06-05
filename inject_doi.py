import json
import os
import re
from datetime import datetime

def main():
    cache_file = "doi_cache.json"
    if not os.path.exists(cache_file):
        print("No DOI cache found. Skipping injection.")
        return
    with open(cache_file, "r") as f:
        cache = json.load(f)
    if not cache:
        print("DOI cache empty. Skipping injection.")
        return
    doi = list(cache.values())[0]

    today = datetime.utcnow().strftime("%Y-%m-%d")
    article_file = f"Journal/review-{today}.html"
    if not os.path.exists(article_file):
        print(f"Article file {article_file} not found.")
        return

    with open(article_file, "r", encoding="utf-8") as f:
        html = f.read()

    # Replace the placeholder span content
    pattern = r'(<span id="doi-value">)(.*?)(</span>)'
    replacement = rf'\g<1>{doi}\g<3>'
    new_html = re.sub(pattern, replacement, html)

    # Add meta tag for citation
    meta_doi = f'<meta name="citation_doi" content="{doi}">'
    if 'citation_doi' not in new_html:
        new_html = new_html.replace('</head>', f'{meta_doi}\n</head>')

    with open(article_file, "w", encoding="utf-8") as f:
        f.write(new_html)
    print(f"Injected DOI {doi} into {article_file}")

if __name__ == "__main__":
    main()
