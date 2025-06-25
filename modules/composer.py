from markdown2 import markdown
from weasyprint import HTML, CSS

STYLE = CSS(string="""
h1 { text-align:center; }
h2 { page-break-before:always; }
li { margin-bottom:4px; }
""")

def make_pdf(markdown_text: str) -> bytes:
    html = markdown(markdown_text)
    return HTML(string=html).write_pdf(stylesheets=[STYLE])
