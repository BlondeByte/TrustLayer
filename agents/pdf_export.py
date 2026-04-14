"""
TrustLayer PDF Export
Converts markdown reports to branded PDFs automatically.
Drop this in your TrustLayer root folder.
Requires: pip3 install weasyprint markdown
"""

import os
import logging
import markdown

logging.basicConfig(
    filename="trustlayer_audit.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def audit_log(event: str, detail: str = ""):
    logging.info(f"{event} | {detail}")

# ============================================================
# BRANDED CSS
# ============================================================

TRUSTLAYER_CSS = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Inter:wght@300;400;600;700&display=swap');

* { box-sizing: border-box; margin: 0; padding: 0; }

@page {
    size: A4;
    margin: 40px 48px;
    @bottom-right {
        content: "TrustLayer by blondebytesecurity — Page " counter(page) " of " counter(pages);
        font-family: 'JetBrains Mono', monospace;
        font-size: 8px;
        color: #6b7280;
    }
}

body {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    line-height: 1.7;
    color: #1f2937;
    background: #ffffff;
}

/* Header bar */
.header {
    background: #0a0a0a;
    color: #f59e0b;
    padding: 16px 24px;
    margin-bottom: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-radius: 2px;
}

.header-brand {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.15em;
}

.header-sub {
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    color: #6b7280;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

h1 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 18px;
    font-weight: 700;
    color: #0a0a0a;
    margin-bottom: 8px;
    padding-bottom: 12px;
    border-bottom: 2px solid #f59e0b;
}

h2 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    font-weight: 700;
    color: #0a0a0a;
    margin-top: 28px;
    margin-bottom: 12px;
    padding: 8px 12px;
    background: #f9fafb;
    border-left: 3px solid #f59e0b;
    letter-spacing: 0.05em;
}

h3 {
    font-family: 'Inter', sans-serif;
    font-size: 11px;
    font-weight: 600;
    color: #374151;
    margin-top: 16px;
    margin-bottom: 8px;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

p {
    margin-bottom: 10px;
    color: #374151;
}

ul, ol {
    padding-left: 20px;
    margin-bottom: 10px;
}

li {
    margin-bottom: 4px;
    color: #374151;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 16px 0;
    font-size: 10px;
}

th {
    background: #0a0a0a;
    color: #f59e0b;
    padding: 8px 12px;
    text-align: left;
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

td {
    padding: 7px 12px;
    border-bottom: 1px solid #e5e7eb;
    color: #374151;
}

tr:nth-child(even) td {
    background: #f9fafb;
}

/* Code/monospace */
code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    background: #f3f4f6;
    padding: 2px 6px;
    border-radius: 2px;
    color: #1f2937;
}

/* Blockquotes / callouts */
blockquote {
    border-left: 3px solid #f59e0b;
    padding: 8px 16px;
    margin: 16px 0;
    background: #fffbeb;
    color: #92400e;
    font-size: 10px;
}

/* HR divider */
hr {
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 20px 0;
}

/* Strong */
strong {
    color: #0a0a0a;
    font-weight: 600;
}

/* Em */
em {
    color: #6b7280;
}

/* Disclaimer box */
.disclaimer {
    background: #f9fafb;
    border: 1px solid #e5e7eb;
    border-top: 2px solid #6b7280;
    padding: 12px 16px;
    margin-top: 24px;
    font-size: 9px;
    color: #6b7280;
    font-family: 'JetBrains Mono', monospace;
}

/* Footer */
.footer {
    margin-top: 32px;
    padding-top: 12px;
    border-top: 1px solid #e5e7eb;
    font-family: 'JetBrains Mono', monospace;
    font-size: 8px;
    color: #9ca3af;
    text-align: center;
    letter-spacing: 0.1em;
}
"""

# ============================================================
# HTML TEMPLATE
# ============================================================

def build_html(report_markdown: str, timestamp: str) -> str:
    """
    Converts markdown report to branded HTML for PDF rendering.
    """
    # Convert markdown to HTML
    md_content = markdown.markdown(
        report_markdown,
        extensions=["tables", "fenced_code", "nl2br"]
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <style>{TRUSTLAYER_CSS}</style>
</head>
<body>
    <div class="header">
        <div>
            <div class="header-brand">TRUST<span style="color:#6b7280">LAYER</span></div>
            <div class="header-sub">Content Intelligence System</div>
        </div>
        <div style="text-align:right">
            <div class="header-sub">by blondebytesecurity</div>
            <div class="header-sub" style="color:#f59e0b">{timestamp}</div>
        </div>
    </div>

    {md_content}

    <div class="footer">
        TRUSTLAYER · BLONDEBYTESECURITY · CONTENT INTELLIGENCE PLATFORM
    </div>
</body>
</html>"""

    return html


# ============================================================
# MAIN EXPORT FUNCTION
# ============================================================

def export_pdf(report_markdown: str, filepath_md: str) -> str | None:
    """
    Takes the markdown report and filepath of the saved .md file.
    Generates a PDF in the same reports/ directory.
    Returns PDF filepath or None on failure.
    """
    try:
        from weasyprint import HTML, CSS
        from weasyprint.text.fonts import FontConfiguration
    except (ImportError, OSError):
        print("[PDF Export] weasyprint not installed — skipping PDF generation.")
        print("[PDF Export] Run: pip3 install weasyprint markdown")
        audit_log("PDF_EXPORT_SKIPPED", "weasyprint not installed")
        return None

    try:
        # Derive PDF path from MD path
        pdf_filepath = filepath_md.replace(".md", ".pdf")

        # Extract timestamp from filename
        timestamp = os.path.basename(filepath_md).replace("trustlayer_report_", "").replace(".md", "")
        timestamp_display = f"{timestamp[:4]}-{timestamp[4:6]}-{timestamp[6:8]} {timestamp[9:11]}:{timestamp[11:13]}:{timestamp[13:15]}"

        # Build HTML
        html_content = build_html(report_markdown, timestamp_display)

        # Render PDF
        font_config = FontConfiguration()
        html = HTML(string=html_content)
        css = CSS(string=TRUSTLAYER_CSS, font_config=font_config)
        html.write_pdf(pdf_filepath, font_config=font_config)

        print(f"[PDF Export] ✅ PDF saved: {pdf_filepath}")
        audit_log("PDF_EXPORT_SUCCESS", f"filepath={pdf_filepath}")
        return pdf_filepath

    except Exception as e:
        print(f"[PDF Export] ⚠️  PDF generation failed: {str(e)}")
        audit_log("PDF_EXPORT_FAILED", f"error={str(e)}")
        return None