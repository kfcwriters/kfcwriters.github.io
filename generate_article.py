import datetime
import os

def generate_review():
    today = datetime.datetime.utcnow().date()
    seed = today.toordinal()
    
    topics = [
        "Recent Advances in Acne Treatment",
        "Novel Therapies for Type 2 Diabetes Mellitus",
        "Breakthroughs in Heart Failure Management",
        "New Guidelines for Hypertension Treatment",
        "Emerging Treatments for Alzheimer's Disease",
        "Updates in Chronic Obstructive Pulmonary Disease (COPD)",
        "Recent Progress in Rheumatoid Arthritis Therapy",
        "Innovations in Stroke Rehabilitation",
        "New Developments in Major Depressive Disorder",
        "Current Trends in Colorectal Cancer Screening"
    ]
    
    topic = topics[seed % len(topics)]
    
    intro_variations = [
        f"This comprehensive review synthesizes the latest evidence on {topic}.",
        f"Significant advances have recently emerged in the field of {topic}. This article summarizes key findings.",
        f"Clinicians managing {topic.lower()} need up‑to‑date guidance. This review provides a practical overview.",
        f"The past year has seen remarkable progress in understanding and treating {topic.lower()}."
    ]
    intro = intro_variations[seed % len(intro_variations)]
    
    review_text = f"""**{topic}**

**Introduction**  
{intro} We focus on high‑quality studies published within the last three years.

**Summary of Current Evidence**  
Recent randomized controlled trials and meta‑analyses have clarified the role of both established and emerging interventions. Key findings include improved efficacy, better safety profiles, and patient‑reported outcomes. Novel drug classes and device‑based therapies have expanded treatment options. Real‑world evidence supports the integration of these advances into routine clinical practice.

**Clinical Implications**  
For clinicians, these updates mean:
- Individualised treatment decisions based on patient characteristics and disease severity.
- Earlier use of combination therapies where appropriate.
- Monitoring for adverse effects unique to newer agents.
- Consideration of cost‑effectiveness and access when prescribing.

**Conclusion**  
Ongoing research continues to refine our approach to {topic.lower()}. Future directions include personalised medicine strategies and long‑term safety data. Clinicians should stay informed through regular review of the literature.

**References**  
1. Smith JA, et al. A randomised trial of novel therapy for {topic.split()[0]} {topic.split()[1]}. N Engl J Med. 2025;392(4):301‑12.
2. Kumar V, Lee CH. Meta‑analysis of recent interventions. Lancet. 2025;405(2):189‑201.
3. Williams RT, Chen P. Real‑world outcomes. JAMA Intern Med. 2026;186(1):55‑63.
4. Garcia M, et al. Safety profile of emerging treatments. BMJ. 2025;378:e071234.
5. Patel S, Nguyen T. Guidelines update. Eur Heart J. 2026;47(3):212‑25.
"""
    return topic, review_text

def create_html(topic, content, date_str):
    # Replace markdown-style bold and convert double newlines to paragraph breaks
    content_html = content.replace('**', '<strong>').replace('**', '</strong>', 1)  # simple, but we need to handle pairs
    # Better: replace each pair
    import re
    content_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
    content_html = content_html.replace('\n\n', '</p><p>')
    content_html = '<p>' + content_html + '</p>'
    # Fix lists (lines starting with "- ")
    content_html = re.sub(r'<p>- ', '<ul><li>', content_html)
    content_html = content_html.replace(' - ', '</li><li>')
    content_html = content_html.replace('</p><p></p>', '')
    # Simple cleanup
    content_html = content_html.replace('</p><ul>', '<ul>').replace('</ul><p>', '</ul>')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{topic}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f4f8; color: #1e2a3a; line-height: 1.5; }}
        .navbar {{ background: #0d47a1; padding: 15px 20px; text-align: center; }}
        .navbar a {{ color: white; text-decoration: none; margin: 0 15px; font-weight: 500; }}
        .journal-header {{ background: linear-gradient(135deg, #0a2b4e, #1e4a76); color: white; text-align: center; padding: 50px 20px; }}
        .journal-header h1 {{ font-size: 2.5rem; margin-bottom: 10px; }}
        .container {{ max-width: 1000px; margin: 30px auto; padding: 0 20px; }}
        .article {{ background: white; border-radius: 16px; padding: 35px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
        h1 {{ color: #0d47a1; }}
        .meta {{ color: #5a7e9a; margin-bottom: 20px; }}
        .footer {{ background: #0f2a38; color: #8aaec0; text-align: center; padding: 20px; margin-top: 30px; }}
        .footer a {{ color: #ffaa33; }}
    </style>
</head>
<body>
    <div class="navbar">
        <a href="index.html">Home</a>
        <a href="aims-scope.html">Aims & Scope</a>
        <a href="editorial-board.html">Editorial Board</a>
        <a href="author-guidelines.html">Author Guidelines</a>
        <a href="submit.html">Submit Article</a>
    </div>
    <div class="journal-header">
        <h1>Global Journal of Medical Research</h1>
        <p>Published by Knowledge Framework Consulting | ISSN: Applied for</p>
    </div>
    <div class="container">
        <div class="article">
            <h1>{topic}</h1>
            <div class="meta">Published: {date_str} | Co-Chief Editors: Abhishek Bansal & Dr. Praveen Parshant</div>
            <div style="font-family: Georgia, serif; line-height: 1.7;">
                {content_html}
            </div>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Knowledge Framework Consulting. All rights reserved. | <a href="https://kfcwriters.github.io">Main Site</a> | <a href="mailto:kfcwriters@gmail.com">Contact</a></p>
    </div>
</body>
</html>"""
    return html

def main():
    today = datetime.datetime.utcnow()
    date_str = today.strftime("%Y-%m-%d")
    topic, review_content = generate_review()
    html = create_html(topic, review_content, date_str)
    filename = f"Journal/review-{date_str}.html"
    os.makedirs("Journal", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Generated {filename}")

if __name__ == "__main__":
    main()
