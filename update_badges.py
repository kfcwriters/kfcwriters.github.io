import json
from bs4 import BeautifulSoup

def main():
    # Read the current index.html
    with open("Journal/index.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find the sidebar (the <div class="sidebar">)
    sidebar = soup.find("div", class_="sidebar")
    if not sidebar:
        print("Sidebar not found in index.html")
        return

    # Remove any existing badge section (optional: find a specific div)
    existing_badges = sidebar.find("div", class_="journal-badges")
    if existing_badges:
        existing_badges.decompose()

    # Build new badge HTML
    badges_html = """
    <div class="journal-badges" style="margin: 20px 0;">
        <h3>Credibility</h3>
        <ul>
            <li>✓ DOI assigned to each article (via Zenodo)</li>
            <li>✓ Compliant with COPE guidelines</li>
            <li>✓ Indexing: Google Scholar (applied), Crossref (in progress)</li>
            <li>✓ Archiving: PKP PN / LOCKSS (planned) + Zenodo monthly</li>
        </ul>
    </div>
    """
    # Insert the badges after the journal information heading
    # We'll find the first <h3> (Journal Information) and insert after it
    info_heading = sidebar.find("h3", string="Journal Information")
    if info_heading:
        new_badges = BeautifulSoup(badges_html, "html.parser")
        info_heading.insert_after(new_badges)
    else:
        # Fallback: append to sidebar
        sidebar.append(BeautifulSoup(badges_html, "html.parser"))

    # Also add a line about DOIs being live if we have a cache
    try:
        with open("doi_cache.json", "r") as f:
            cache = json.load(f)
            if cache:
                latest_doi = list(cache.values())[-1]
                doi_line = soup.new_tag("p")
                doi_line.string = f"Latest article DOI: {latest_doi}"
                # Insert near the top of the main content? optional.
    except:
        pass

    with open("Journal/index.html", "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("Updated badges on homepage.")

if __name__ == "__main__":
    main()
