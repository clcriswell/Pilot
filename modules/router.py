import random
import os
import streamlit as st
from functools import lru_cache
from modules import tools  # to access semantic_search, fetch_image, summarize_text
import json
import datetime

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

        # Base system prompt describing assistant role and tools
        self.base_system_prompt = (
            "You are a knowledgeable R&D assistant. You have access to the following tools: "
            "semantic_search (to lookup information), fetch_image (to find relevant images), "
            "summarize_text (to condense information). Use these tools when appropriate, and provide clear, concise answers."
        )
        self.base_messages = [{"role": "system", "content": self.base_system_prompt}]

        # Running conversation history (excluding the fixed system prompt)
        self.conversation: list[dict] = []

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
        """Dispatch the function call to the appropriate tool and log the call."""
        func = self.tools.get(name)
        if not func:
            raise ValueError(f"Unknown tool: {name}")

        result = func(**args)

        log_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "tool": name,
            "arguments": args,
            "result": result if len(str(result)) <= 200 else str(result)[:200] + "...",
        }
        try:
            log_path = "vault/audit_log.jsonl"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as logf:
                logf.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Logging error: {e}")

        return result

    def ask(self, prompt: str, domain: str, model_override: str | None = None) -> tuple[str, str]:
        # Use GPT-4 by default for function-calling capable queries
        model_name = model_override or "gpt-4"

        client = openai.OpenAI(api_key=self.api_keys[self.key_index])

        # Build the message list with a fixed system prefix and running conversation
        messages = self.base_messages + self.conversation + [{"role": "user", "content": prompt}]

        # Summarize older conversation if it becomes too long
        # Handle messages that may have `None` as the content (e.g. assistant
        # function calls) by treating them as empty strings when counting
        # characters.
        total_chars = sum(len(m.get("content") or "") for m in messages)
        if total_chars > 10000:
            convo_text = ""
            for m in self.conversation:
                role = m.get("role")
                content = m.get("content", "")
                if role in ("user", "assistant") and content:
                    convo_text += f"{role}: {content}\n"
            summary = tools.summarize_text(convo_text, sentences=5)
            summary_message = {
                "role": "system",
                "content": f"(Summary of earlier conversation: {summary})",
            }
            self.conversation = [summary_message]
            messages = self.base_messages + self.conversation + [{"role": "user", "content": prompt}]

        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            functions=self.function_schemas,
            function_call="auto",
        )
        msg = response.choices[0].message

        conversation = messages[:]
        while getattr(msg, "function_call", None):
            func_name = msg.function_call.name
            args_json = getattr(msg.function_call, "arguments", "{}")
            try:
                args = json.loads(args_json)
            except json.JSONDecodeError:
                args = {}

            result = self.call_tool(func_name, args)

            conversation.append({"role": "assistant", "content": None, "function_call": msg.function_call.model_dump() if hasattr(msg.function_call, "model_dump") else {"name": msg.function_call.name, "arguments": args_json}})
            conversation.append({"role": "function", "name": func_name, "content": str(result)})

            response = client.chat.completions.create(
                model=model_name,
                messages=conversation,
                functions=self.function_schemas,
                function_call="auto",
            )
            msg = response.choices[0].message

        answer = (msg.content or "").strip()
        conversation.append({"role": "assistant", "content": answer})
        # Persist conversation history (excluding the fixed system prompt)
        self.conversation = conversation[1:]

        self.key_index = (self.key_index + 1) % len(self.api_keys)
        return answer, model_name

    async def ask_async(self, prompt: str, domain: str) -> tuple[str, str]:
        """Async version of ask() for concurrent execution."""
        model_name = "gpt-4"
        key = self.api_keys[self.key_index]
        self.key_index = (self.key_index + 1) % len(self.api_keys)

        messages = [
            {"role": "system", "content": self.base_system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            response = await openai.ChatCompletion.acreate(
                model=model_name,
                messages=messages,
                functions=getattr(self, "function_schemas", None),
                function_call="auto",
                api_key=key,
            )
        except Exception as e:
            return f"Error: {e}", model_name

        msg = response["choices"][0]["message"]
        conversation = messages[:]
        while getattr(msg, "function_call", None):
            func_name = msg.function_call.name
            args_json = getattr(msg.function_call, "arguments", "{}")
            try:
                args = json.loads(args_json)
            except json.JSONDecodeError:
                args = {}

            result = self.call_tool(func_name, args)
            conversation.append({"role": "assistant", "content": None, "function_call": msg.function_call.model_dump() if hasattr(msg.function_call, "model_dump") else {"name": msg.function_call.name, "arguments": args_json}})
            conversation.append({"role": "function", "name": func_name, "content": str(result)})

            try:
                response = await openai.ChatCompletion.acreate(
                    model=model_name,
                    messages=conversation,
                    functions=self.function_schemas,
                    function_call="auto",
                    api_key=key,
                )
            except Exception as e:
                return f"Error after function call: {e}", model_name

            msg = response["choices"][0]["message"]

        answer = (getattr(msg, "content", "") or "").strip()
        return answer, model_name
