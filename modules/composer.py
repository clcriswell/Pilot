
from fpdf import FPDF
import io


def _latin1(text: str) -> str:
    """Return *text* encoded to latin-1, replacing unsupported chars."""
    return text.encode("latin-1", "replace").decode("latin-1")
def make_pdf(report_text: str) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    lines = report_text.splitlines()
    if lines:
        pdf.cell(0, 10, _latin1(lines[0]), ln=1, align='C')
    pdf.set_font("Arial", '', 12)
    for line in lines[1:]:
        if line.strip() == "":
            pdf.ln(4)
        elif all(c == '=' for c in line) or all(c == '-' for c in line):
            continue
        elif line.endswith("Considerations") or line.startswith("Details on") or line == "Conclusion":
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 8, _latin1(line), ln=1)
            pdf.set_font("Arial", '', 12)
        else:
            pdf.multi_cell(0, 8, _latin1(line))
    buffer = io.BytesIO()
    pdf.output(buffer)
    return buffer.getvalue()
