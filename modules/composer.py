from markdown2 import markdown
import unicodedata

try:
    from weasyprint import HTML, CSS
    _WEASYPRINT_AVAILABLE = True
except Exception:  # missing system deps like libpango
    from fpdf import FPDF
    _WEASYPRINT_AVAILABLE = False

STYLE = None
if _WEASYPRINT_AVAILABLE:
    STYLE = CSS(string="""
h1 { text-align:center; }
h2 { page-break-before:always; }
li { margin-bottom:4px; }
""")

def _make_pdf_weasy(html: str) -> bytes:
    """Generate a PDF using WeasyPrint if available."""
    return HTML(string=html).write_pdf(stylesheets=[STYLE])


def _make_pdf_fpdf(markdown_text: str) -> bytes:
    """Simplistic fallback PDF generator using FPDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in markdown_text.splitlines():
        safe_line = unicodedata.normalize("NFKD", line).encode("latin-1", "replace").decode("latin-1")
        pdf.multi_cell(0, 10, safe_line)
    return bytes(pdf.output(dest="S"))


def make_pdf(markdown_text: str) -> bytes:
    """Convert markdown text to PDF using WeasyPrint or FPDF."""
    html = markdown(markdown_text)
    if _WEASYPRINT_AVAILABLE:
        return _make_pdf_weasy(html)
    return _make_pdf_fpdf(markdown_text)
