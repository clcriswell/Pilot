"""Utility functions accessible via OpenAI function calling."""

from __future__ import annotations

from typing import List


def semantic_search(query: str) -> str:
    """Mock semantic search returning a simple string for the query."""
    return f"Results for '{query}' from the knowledge base."


def fetch_image(query: str) -> str:
    """Return a fake image URL for the given query."""
    safe = query.strip().replace(" ", "_")
    return f"https://example.com/images/{safe}.png"


def summarize_text(text: str, sentences: int = 2) -> str:
    """Return the first few sentences of the text as a naive summary."""
    if sentences <= 0:
        return ""
    # Split by sentence terminators for simplicity
    import re

    parts = re.split(r"(?<=[.!?]) +", text)
    summary = " ".join(parts[:sentences])
    return summary.strip()
