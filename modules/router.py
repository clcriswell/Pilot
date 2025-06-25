import random
import os
import streamlit as st
from functools import lru_cache

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
    """Return API keys from Streamlit secrets, env vars or fallback config."""
    keys = st.secrets.get("openai_api_keys")
    if isinstance(keys, str):
        keys = [k.strip() for k in keys.split(',') if k.strip()]
    if isinstance(keys, list) and keys:
        return list(keys)

    env_keys = os.environ.get("OPENAI_API_KEYS") or os.environ.get("OPENAI_API_KEY")
    if isinstance(env_keys, str):
        parsed = [k.strip() for k in env_keys.split(',') if k.strip()]
        if parsed:
            return parsed

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

    @lru_cache(maxsize=128)
    def _cached_completion(self, prompt: str, model_name: str) -> str:
        client = openai.OpenAI(api_key=self.api_keys[self.key_index])
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def ask(self, prompt: str, domain: str, model_override: str | None = None) -> str:
        model_name = model_override or ("gpt-4o-mini" if domain.lower() == "sensors" else "gpt-3.5-turbo")
        # Use current key then rotate for next call
        answer = self._cached_completion(prompt, model_name)
        self.key_index = (self.key_index + 1) % len(self.api_keys)
        return answer
