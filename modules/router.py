
import random
import streamlit as st

try:
    import openai
except ModuleNotFoundError as e:
    openai = None

try:
    from config.config import OPENAI_API_KEYS as LOCAL_KEYS  # user-provided keys
except ImportError:
    try:
        from config.config_template import OPENAI_API_KEYS as LOCAL_KEYS  # placeholder list (empty)
    except ImportError:
        LOCAL_KEYS = []

def _load_api_keys() -> list:
    """Return API keys from Streamlit secrets or fallback config."""
    keys = st.secrets.get("openai_api_keys")
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split(',') if k.strip()]
    if isinstance(keys, list) and keys:
        return list(keys)
    return LOCAL_KEYS

class QueryRouter:
    """Rotate through API keys (and optionally proxies) for each outbound query."""

    def __init__(self):
        if openai is None:
            raise ModuleNotFoundError("The 'openai' package is required but not installed.")
        self.api_keys = _load_api_keys()
        if not self.api_keys:
            raise RuntimeError(
                "No OpenAI API keys found. Add them to Streamlit secrets or config/config.py."
            )
        self.key_index = random.randrange(len(self.api_keys))

    def ask(self, prompt: str, domain: str) -> str:
        # Rotate key
        key = self.api_keys[self.key_index]
        self.key_index = (self.key_index + 1) % len(self.api_keys)
        client = openai.OpenAI(api_key=key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
