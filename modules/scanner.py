
import re
def scan_content(text: str) -> str:
    """Remove simple HTML/XML tags as basic sanitization."""
    return re.sub(r'<[^>]+>', '', text)
