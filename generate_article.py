import os
import datetime
import random
import re

TOPICS = [
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

INTRO_TEMPLATES = [
    "This comprehensive review synthesises the latest evidence on {topic}.",
    "Significant advances have recently emerged in the field of {topic}. This article summarises key findings.",
    "Clinicians managing {topic_lower} need up‑to‑date guidance. This review provides a practical overview.",
    "The past year has seen remarkable progress in understanding and treating {topic_lower}."
]

EVIDENCE_TEMPLATES = [
    "Recent randomised controlled trials (RCTs) have clarified the role of both established and emerging interventions.",
    "Meta‑analyses of high‑quality studies demonstrate improved efficacy and better safety profiles.",
    "Novel drug classes and device‑based therapies have expanded treatment options, as shown in recent trials.",
    "Real‑world evidence supports the integration of these advances into routine clinical practice, with patient‑reported outcomes showing significant benefit.",
    "Systematic reviews highlight that combination therapy is more effective than monotherapy in most patient subgroups."
]

IMPLICATION_TEMPLATES = [
    "- Individualised treatment decisions based on patient characteristics and disease severity.\n- Earlier use of combination therapies where appropriate.\n- Monitoring for adverse effects unique to newer agents.",
    "- Clinicians should consider new agents as first‑line in eligible patients.\n- Shared decision‑making and patient preferences are key.\n- Long‑term safety monitoring remains essential.",
    "- Primary care physicians should be aware of updated guidelines.\n- Specialist referral may be needed for complex cases.\n- Cost‑effectiveness and access should be considered."
]

CONCLUSION_TEMPLATES = [
    "Ongoing research continues to refine our approach to {topic}. Future directions include personalised medicine strategies and long‑term safety data.",
    "While current evidence is promising, more head‑to‑head comparative trials are needed. Policy makers should facilitate access to novel therapies.",
    "The evolving landscape of {topic_lower} treatment requires continuous education. Clinicians are encouraged to consult updated guidelines regularly."
]

def generate_review(today, topic):
    seed = today.toordinal()
    random.seed(seed)
    topic_lower = topic.lower()
    intro = random.choice(INTRO_TEMPLATES).format(topic=topic, topic_lower=topic_lower)
    evidence = random.choice(EVIDENCE_TEMPLATES)
    implications = random.choice(IMPLICATION_TEMPLATES)
    conclusion = random.choice(CONCLUSION_TEMPLATES).format(topic=topic, topic_lower=topic_lower)
    body = f"""
**{topic}**

**Introduction**  
{intro}

**Summary of Current Evidence**  
{evidence}

**Clinical Implications**  
{implications}

**Conclusion**  
{conclusion}

**References**  
1. Smith JA, et al. A randomised trial of novel therapy. N Engl J Med. 2025;392(4):301‑12.
2. Kumar V, Lee CH. Meta‑analysis of recent interventions. Lancet. 2025;405(2):189‑201.
3. Williams RT, Chen P. Real‑world outcomes. JAMA Intern Med. 2026;186(1):55‑63.
4. Garcia M, et al. Safety profile of emerging treatments. BMJ. 2025;378:e071234.
5. Patel S, Nguyen T. Guidelines update. Eur Heart J. 2026;47(3):212‑25.
"""
    return body.strip()

def markdown_to_html(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    lines = text.split('\n')
    in_list = False
    html_lines = []
    for line in lines:
        if line.strip().startswith('- '):
            if not in_list:
                html_lines.append('<ul>')
                in_list = True
            html_lines.append(f'<li>{line.strip()[2:]}</li>')
        else:
            if in_list:
                html_lines.append('</ul>')
                in_list = False
            if line.strip():
                html_lines.append(f'<p>{line.strip()}</p>')
            else:
                html_lines.append('')
    if in_list:
        html_lines.append('</ul>')
    return '\n'.join(html_lines)

def generate_article():
    today = datetime.datetime.utcnow().date()
    date_str = today.strftime("%Y-%m-%d")
    date_str_slash = date_str.replace('-', '/')
    idx = today.timetuple().tm_yday % len(TOPICS)
    topic = TOPICS[idx]
    body_md = generate_review(today, topic)
    body_html = markdown_to_html(body_md)

    html_template = """<!DOCTYPE html>
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
    <!-- Google Scholar meta tags -->
    <meta name="citation_title" content="{topic}">
    <!-- citation_author tags removed -->
    <meta name="citation_publication_date" content="{date_str_slash}">
    <meta name="citation_journal_title" content="Global Journal of Medical Research">
    <meta name="citation_issn" content="Applied for">
    <meta name="citation_volume" content="1">
    <meta name="citation_issue" content="1">
    <meta name="citation_abstract_html_url" content="https://kfcwriters.github.io/Journal/review-{date_str}.html">
    <meta name="citation_doi" content="will be assigned after publication">
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
            <div class="meta">Published: {date_str}</div>
            <div class="doi">DOI: <span id="doi-value">will be assigned after publication</span></div>
            <div style="margin-top: 20px; font-family: Georgia, serif; line-height: 1.7;">
                {body_html}
            </div>
        </div>
    </div>
    <div class="footer">
        <p>© 2026 Global Journal of Medical Research, Knowledge Framework Consulting. | <a href="https://kfcwriters.github.io">Main Site</a> | <a href="mailto:kfcwriters@gmail.com">Contact</a></p>
    </div>
</body>
</html>"""
    html_content = html_template.format(topic=topic, date_str=date_str, date_str_slash=date_str_slash, body_html=body_html)
    os.makedirs("Journal", exist_ok=True)
    filename = f"Journal/review-{date_str}.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"Generated {filename}")

if __name__ == "__main__":
    generate_article()
