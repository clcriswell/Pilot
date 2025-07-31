"""
Advanced Synthesizer – multi format, template driven, with QA and versioning.
"""

import hashlib, datetime, os, re, json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
from modules import polish

TEMPLATE_DIR = Path("synthesizer_templates")
DRAFT_DIR = Path("vault/drafts")
DRAFT_DIR.mkdir(parents=True, exist_ok=True)

env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(enabled_extensions=("html",))
)

# --------------------------------------------------------------------- #
# Helper – template inference
# --------------------------------------------------------------------- #
def choose_template_type(prompt: str) -> str:
    p = prompt.lower()
    if "strategic plan" in p or "business plan" in p:
        return "strategic_plan"
    if "design spec" in p or "architecture" in p or any(k in p for k in ("design", "build", "develop")):
        return "technical_spec"
    if "prototype" in p or "code" in p:
        return "code_prototype"
    if "summary" in p or "research" in p:
        return "research_summary"
    if "slides" in p or "presentation" in p:
        return "slide_deck"
    return "research_summary"  # safe default

# --------------------------------------------------------------------- #
# Helper – QA checks
# --------------------------------------------------------------------- #
PLACEHOLDERS = re.compile(r"(TBD|to be decided|<placeholder>|lorem ipsum|\?\?\?)", re.I)

def qa_check(text: str, required_sections=None):
    issues = []
    if PLACEHOLDERS.search(text):
        issues.append("Placeholder text detected.")
    if required_sections:
        for sec in required_sections:
            if sec not in text:
                issues.append(f"Missing section: {sec}")
    return issues

# --------------------------------------------------------------------- #
# Main synthesize entry point
# --------------------------------------------------------------------- #
def synthesize(project_name: str,
               user_prompt: str,
               data: dict,
               artifacts: dict | None = None) -> str:
    """
    project_name – short title
    user_prompt  – original user text
    data         – dict of cleaned/processed domain results
    artifacts    – optional dict: {"architecture_diagram": "vault/…/arch.png", "code": "...", …}
    Returns markdown string.
    """
    template_key = choose_template_type(user_prompt)
    template_path = f"{template_key}.md.j2"
    template = env.get_template(template_path)

    ctx = {"project_name": project_name, **data, **(artifacts or {})}
    draft = template.render(ctx)

    # ----------------------------------------------------- #
    # internal QA / placeholder scan
    # ----------------------------------------------------- #
    required = None
    if template_key == "technical_spec":
        required = ["Requirements", "Architecture", "Feasibility"]
    issues = qa_check(draft, required)

    if issues:
        warn_block = "\n".join(f"> **QA Warning:** {issue}" for issue in issues)
        draft += "\n\n" + warn_block

    # ----------------------------------------------------- #
    # optional local LLM polish
    # ----------------------------------------------------- #
    draft = polish.polish(draft)

    # ----------------------------------------------------- #
    # versioning
    # ----------------------------------------------------- #
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    fname = DRAFT_DIR / f"draft_{ts}.md"
    fname.write_text(draft, encoding="utf-8")
    sha = hashlib.sha256(draft.encode()).hexdigest()
    with open(DRAFT_DIR / "drafts_log.txt", "a", encoding="utf-8") as log:
        log.write(f"{ts} {fname.name} SHA256:{sha}\n")

    return draft
