from markdown2 import markdown
from weasyprint import HTML


def make_pdf(report_md: str) -> bytes:
    html = markdown(report_md)
    pdf_bytes = HTML(string=html).write_pdf()
    return pdf_bytes
