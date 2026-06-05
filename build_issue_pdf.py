# scripts/build_issue_pdf.py
import os
import re
import datetime
import requests
from bs4 import BeautifulSoup

def main():
    # Determine previous month and year
    now = datetime.datetime.utcnow()
    first_of_this_month = datetime.datetime(now.year, now.month, 1)
    last_month = first_of_this_month - datetime.timedelta(days=1)
    year = last_month.year
    month = last_month.month
    # Save environment variables for the workflow
    with open(os.environ['GITHUB_ENV'], 'a') as f:
        f.write(f"YEAR={year}\nMONTH={month:02d}\n")

    # List all review-*.html files in Journal/
    files = [f for f in os.listdir("Journal") if f.startswith("review-") and f.endswith(".html")]
    # Filter by date: extract YYYY-MM-DD from filename
    month_files = []
    for fname in files:
        match = re.search(r'review-(\d{4})-(\d{2})-(\d{2})', fname)
        if match:
            y = int(match.group(1)); m = int(match.group(2))
            if y == year and m == month:
                month_files.append(fname)
    if not month_files:
        print(f"No articles found for {year}-{month:02d}. Skipping PDF.")
        sys.exit(0)

    # Build combined HTML
    combined_html = f"""<!DOCTYPE html>
<html>
<head><title>Global Journal of Medical Research – Volume {year}, Issue {month:02d}</title>
<style>
    body {{ font-family: Georgia, serif; margin: 2rem; line-height: 1.5; }}
    h1 {{ color: #0d47a1; }}
    .article {{ page-break-after: always; margin-bottom: 2rem; }}
</style>
</head>
<body>
    <h1>Global Journal of Medical Research</h1>
    <h2>Volume {year}, Issue {month:02d}</h2>
    <p>Published: {last_month.strftime('%B %Y')}</p>
"""
    for fname in sorted(month_files):
        with open(f"Journal/{fname}", "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            # Extract the main article content (div with class "article")
            article_div = soup.find("div", class_="article")
            if article_div:
                combined_html += f'<div class="article">{article_div.prettify()}</div><hr>'
    combined_html += "</body></html>"

    with open("issue.html", "w", encoding="utf-8") as f:
        f.write(combined_html)
    print(f"Built issue.html for {year}-{month:02d}")

if __name__ == "__main__":
    main()
