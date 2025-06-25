from markdown2 import markdown

try:  # Prefer weasyprint if system deps are available
    from weasyprint import HTML
    _USE_WEASYPRINT = True
except Exception:  # pragma: no cover - fallback when libpango is missing
    from fpdf import FPDF
    _USE_WEASYPRINT = False


def _make_pdf_fpdf(html: str) -> bytes:
    """Create a minimal PDF from HTML using FPDF.

    The HTML is converted to plain text line by line. This avoids external
    dependencies so the application can run in offline environments.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in html.splitlines():
        text = line.strip()
        if text:
            pdf.multi_cell(0, 10, txt=text)
        else:
            pdf.ln(5)
    return pdf.output(dest="S").encode("latin-1")


def make_pdf(report_md: str) -> bytes:
    html = markdown(report_md)
    if _USE_WEASYPRINT:
        return HTML(string=html).write_pdf()
    return _make_pdf_fpdf(html)
