
import os, openai, random
try:
    from config.config import OPENAI_API_KEYS  # user-provided keys
except ImportError:
    try:
        from config.config_template import OPENAI_API_KEYS  # placeholder list (empty)
    except ImportError:
        OPENAI_API_KEYS = []

class QueryRouter:
    """Rotate through API keys (and optionally proxies) for each outbound query."""
    def __init__(self):
        if not OPENAI_API_KEYS:
            raise RuntimeError("No OpenAI API keys found. Please populate config/config.py.")
        self.api_keys = OPENAI_API_KEYS
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
