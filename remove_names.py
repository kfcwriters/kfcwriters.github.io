import os
import re

def clean_article(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    # Remove the two citation_author meta tags
    content = re.sub(r'<meta name="citation_author" content="Abhishek Bansal">\s*', '', content)
    content = re.sub(r'<meta name="citation_author" content="Dr\. Praveen Parshant">\s*', '', content)
    # Remove the "Co-Chief Editors: ..." part from the meta line
    content = re.sub(r' \| Co-Chief Editors: Abhishek Bansal & Dr\. Praveen Parshant', '', content)
    # Also remove from any place where it appears in the sidebar (if any)
    content = re.sub(r'<p><strong>Co-Chief Editors:</strong> Abhishek Bansal & Dr\. Praveen Parshant</p>', '', content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned {filepath}")

def main():
    for fname in os.listdir("Journal"):
        if fname.startswith("review-") and fname.endswith(".html"):
            clean_article(os.path.join("Journal", fname))

if __name__ == "__main__":
    main()
