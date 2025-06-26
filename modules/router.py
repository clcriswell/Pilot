import random
import os
import streamlit as st
from functools import lru_cache
from modules import tools  # to access semantic_search, fetch_image, summarize_text
import json

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
        # Register available tool functions for function calling:
        self.tools = {
            "semantic_search": tools.semantic_search,
            "fetch_image": tools.fetch_image,
            "summarize_text": tools.summarize_text,
        }
        # Define function schemas for GPT-4
        self.function_schemas = [
            {
                "name": "semantic_search",
                "description": "Search the knowledge base for relevant information by keyword.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "The search query text."}
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "fetch_image",
                "description": "Fetch a relevant image URL for a given topic or query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Description of the image to retrieve."}
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "summarize_text",
                "description": "Summarize a given text passage into a shorter form.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "The text content to summarize."},
                        "sentences": {"type": "integer", "description": "Approximate number of sentences for the summary."},
                    },
                    "required": ["text"],
                },
            },
        ]

    @lru_cache(maxsize=128)
    def _cached_completion(self, prompt: str, model_name: str) -> str:
        client = openai.OpenAI(api_key=self.api_keys[self.key_index])
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    def call_tool(self, name: str, args: dict):
        """Dispatch the function call to the appropriate tool and return its result."""
        func = self.tools.get(name)
        if not func:
            raise ValueError(f"Unknown tool: {name}")
        return func(**args)

    def ask(self, prompt: str, domain: str, model_override: str | None = None) -> tuple[str, str]:
        # Use GPT-4 by default for function-calling capable queries
        model_name = model_override or "gpt-4"

        client = openai.OpenAI(api_key=self.api_keys[self.key_index])

        # Build the message list with a system prompt describing the assistant and tools
        messages = [
            {
                "role": "system",
                "content": (
                    "You are a secure R&D assistant. You have access to tools like "
                    "semantic_search (for knowledge base queries), fetch_image (for finding images), "
                    "and summarize_text (for summarizing content). Use tools when needed, and return answers in natural language."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            functions=self.function_schemas,
            function_call="auto",
        )
        msg = response.choices[0].message

        conversation = messages[:]
        while msg.get("function_call"):
            func_name = msg["function_call"]["name"]
            args_json = msg["function_call"].get("arguments", "{}")
            try:
                args = json.loads(args_json)
            except json.JSONDecodeError:
                args = {}

            result = self.call_tool(func_name, args)

            conversation.append({"role": "assistant", "content": None, "function_call": msg["function_call"]})
            conversation.append({"role": "function", "name": func_name, "content": str(result)})

            response = client.chat.completions.create(
                model=model_name,
                messages=conversation,
                functions=self.function_schemas,
                function_call="auto",
            )
            msg = response.choices[0].message

        answer = msg.get("content", "").strip()
        self.key_index = (self.key_index + 1) % len(self.api_keys)
        return answer, model_name
