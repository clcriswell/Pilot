"""
polish.py – optional local LLM rewrite helper.
If transformers / GPU not present it degrades to a no op.
"""

import os

USE_POLISH = os.environ.get("ENABLE_POLISH", "0") == "1"


def polish(text: str) -> str:
    if not USE_POLISH:
        return text  # no op
    try:
        from transformers import pipeline
        # small, local instr model; change to your own if desired
        model_name = os.environ.get("POLISH_MODEL", "google/flan-t5-base")
        rewriter = pipeline("text2text-generation", model=model_name, device=-1)
        prompt = (
            "Rewrite the following text in formal, concise third person style, "
            "eliminate redundancy, and fix grammar:\n\n"
        )
        result = rewriter(prompt + text, max_length=len(text.split()) + 32, truncation=True)
        return result[0]["generated_text"]
    except Exception as e:
        # fallback to original in case model missing
        print("Polish skipped:", e)
        return text
