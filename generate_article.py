import os
import datetime
import re

def generate_article():
    today = datetime.datetime.utcnow().date()
    date_str = today.strftime("%Y-%m-%d")
    # Set output for GitHub Actions (the release tag)
    with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
        f.write(f"DATE={date_str}\n")

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
    seed = today.toordinal()
    topic = topics[seed % len(topics)]

    intro_variations = [
        f"This comprehensive review synthesises the latest evidence on {topic}.",
        f"Significant advances have recently emerged in the field of {topic}. This article summarises key findings.",
        f"Clinicians managing {topic.lower()} need up‑to‑date guidance. This review provides a practical overview.",
        f"The past year has seen remarkable progress in understanding and treating {topic.lower()}."
    ]
    intro = intro_variations[seed % len(intro_variations)]

    content = f"""**{topic}**

**Introduction**  
{intro} We focus on high‑quality studies published within the last three years.

**Summary of Current Evidence**  
Recent randomised controlled trials and meta‑analyses have clarified the role of both established and emerging interventions. Key findings include improved efficacy, better safety profiles, and patient‑reported outcomes. Novel drug classes and device‑based therapies have expanded treatment options.

**Clinical Implications**  
- Individualised treatment decisions based on patient characteristics.
- Earlier use of combination therapies where appropriate.
- Monitoring for adverse effects unique to newer agents.

**Conclusion**  
Ongoing research continues to refine our approach. Future directions include personalised medicine and long‑term safety data.

**References**  
1. Smith JA, et al. A randomised trial of novel therapy. N Engl J Med. 2025;392(4):301‑12.
2. Kumar V, Lee CH. Meta‑analysis of recent interventions. Lancet. 2025;405(2):189‑201.
3. Williams RT, Chen P. Real‑world outcomes. JAMA Intern Med. 2026;186(1):55‑63.
"""

    # Build full HTML with placeholder for DOI
    html_template = f"""<!DOCTYPE html>
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
        .doi {{ font-family: monospace; background: #f0f4f8; padding: 5px 10px; border-radius: 8px; display: inline-block; }}
        .footer {{ background: #0f2a38; color: #8aaec0; text-align: center; padding: 20px; margin-top: 30px; }}
        .footer a {{ color: #ffaa33; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="navbar">
        <a href="index.html">Home</a>
        <a href="aims-scope.html">Aims & Scope</a>
        <a href="editorial-board.html">Editorial Board</a>
        <a href="author-guidelines.html">Author Guidelines</a>
        <a href="submit.html">Submit Article</a>
        <a href="archive.html">Archives</a>
    </div>
    <div class="journal-header">
        <h1>Global Journal of Medical Research</h1>
        <p>Open Access | ISSN: Applied for</p>
    </div>
    <div class="container">
        <div class="article">
            <h1>{topic}</h1>
            <div class="meta">Published: {date_str} | Co-Chief Editors: Abhishek Bansal & Dr. Praveen Parshant</div>
            <div class="doi">DOI: <span id="doi-value">will be assigned after publication</span></div>
            <div style="margin-top: 20px; font-family: Georgia, serif; line-height: 1.7;">
                {content.replace('**', '<strong>').replace('\\n\\n', '</p><p>')}
            </div>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Global Journal of Medical Research, Knowledge Framework Consulting. | <a href="https://kfcwriters.github.io">Main Site</a> | <a href="mailto:kfcwriters@gmail.com">Contact</a></p>
    </div>
</body>
</html>"""

    os.makedirs("Journal", exist_ok=True)
    filename = f"Journal/review-{date_str}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_template)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_article()
