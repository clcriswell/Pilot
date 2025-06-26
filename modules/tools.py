"""Utility functions that can be invoked via OpenAI function calling."""

from __future__ import annotations

import os
import json
import streamlit as st

try:
    import openai
except ModuleNotFoundError:
    openai = None

try:
    import pinecone
except ModuleNotFoundError:
    pinecone = None

# Global Pinecone index handle
_pinecone_index = None


def _init_pinecone():
    """Initialize Pinecone client using credentials from secrets or env vars."""
    global _pinecone_index
    if pinecone is None:
        raise ModuleNotFoundError(
            "The 'pinecone' package is required for semantic_search."
        )

    api_key = st.secrets.get("pinecone_api_key") or os.environ.get("PINECONE_API_KEY")
    env = st.secrets.get("pinecone_env") or os.environ.get("PINECONE_ENV")
    index_name = st.secrets.get("pinecone_index") or os.environ.get("PINECONE_INDEX")
    if not api_key or not env or not index_name:
        raise RuntimeError(
            "Pinecone API key, environment, or index name not configured."
        )

    pinecone.init(api_key=api_key, environment=env)
    _pinecone_index = pinecone.Index(index_name)


def semantic_search(query: str) -> str:
    """Search the vector knowledge base for text relevant to the query."""
    if openai is None:
        raise ModuleNotFoundError("The 'openai' package is required for semantic_search.")

    global _pinecone_index
    if _pinecone_index is None:
        _init_pinecone()

    try:
        client = openai.OpenAI()
        embed_resp = client.embeddings.create(
            input=[query], model="text-embedding-ada-002"
        )
    except Exception as e:
        return f"Embedding error: {e}"

    vector = embed_resp.data[0].embedding

    try:
        result = _pinecone_index.query(vector=vector, top_k=5, include_metadata=True)
    except Exception as e:
        return f"Vector search error: {e}"

    matches = result.get("matches", []) if isinstance(result, dict) else getattr(result, "matches", [])
    if not matches:
        return "No relevant documents found."

    snippets = []
    for match in matches:
        text = None
        if isinstance(match, dict):
            text = match.get("metadata", {}).get("text")
        else:
            meta = getattr(match, "metadata", None)
            if meta:
                text = meta.get("text")
        if text:
            snippets.append(text)

    content = "\n".join(snippets)
    if len(content) > 1000:
        content = content[:1000] + "..."
    return content or "No relevant documents found."


def fetch_image(query: str) -> str:
    """Return a URL of an image loosely related to the query."""
    keywords = query.strip().replace(" ", "%20")
    return f"https://source.unsplash.com/featured/?{keywords}"


def summarize_text(text: str, sentences: int = 3) -> str:
    """Summarize the provided text using the OpenAI API."""
    if openai is None:
        raise ModuleNotFoundError("The 'openai' package is required for summarize_text.")

    summary_prompt = (
        f"Please summarize the following text in about {sentences} sentences:\n\n" """{text}"""
    )
    try:
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7,
        )
    except Exception as e:
        return f"Summarization error: {e}"

    return response.choices[0].message.content.strip()
