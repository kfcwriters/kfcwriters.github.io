from bs4 import BeautifulSoup
import json
import os

def main():
    index_file = "Journal/index.html"
    if not os.path.exists(index_file):
        print("Index file not found. Skipping badges update.")
        return

    with open(index_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    sidebar = soup.find("div", class_="sidebar")
    if not sidebar:
        print("Sidebar not found in index.html")
        return

    existing = sidebar.find("div", class_="journal-badges")
    if existing:
        existing.decompose()

    badges_html = """
    <div class="journal-badges" style="margin: 20px 0;">
        <h3>Journal Credentials</h3>
        <ul>
            <li>✓ DOI assigned to each article (via Zenodo)</li>
            <li>✓ Compliant with COPE guidelines</li>
            <li>✓ Indexing: Google Scholar (applied), Crossref (in progress)</li>
            <li>✓ Archiving: PKP PN / LOCKSS (planned) + Zenodo monthly</li>
        </ul>
    </div>
    """
    new_badges = BeautifulSoup(badges_html, "html.parser")
    info_heading = sidebar.find("h3", string="Journal Information")
    if info_heading:
        info_heading.insert_after(new_badges)
    else:
        sidebar.insert(0, new_badges)

    with open(index_file, "w", encoding="utf-8") as f:
        f.write(str(soup))
    print("Updated badges on homepage.")

if __name__ == "__main__":
    main()
