
# Secure Closed-Loop AI R&D Assistant – Streamlit Pilot

This repository contains a demonstration prototype of a privacy‑preserving R&D assistant.
It splits a high‑level request into domain‑specific queries, routes each query through a
different OpenAI API key for anonymity, sanitizes responses, iteratively fills knowledge gaps,
and compiles a final PDF report – all behind a simple Streamlit UI.

## Quick start

```bash
git clone <your‑repo‑url>
cd secure-rd-assistant
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp config/config_template.py config/config.py   # optional fallback
streamlit run app.py
```

Add your OpenAI key(s) to `.streamlit/secrets.toml` as:

```toml
openai_api_keys = ["sk-...", "sk-..."]
```

Open your browser at `http://localhost:8501`, enter a project description
(e.g. "Design a drone for wildfire detection") and click **Run Secure Research**.
A PDF report will be generated for download once the loop completes.
