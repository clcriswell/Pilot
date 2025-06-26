
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

You can also provide keys via environment variables when running locally:

```bash
export OPENAI_API_KEY="sk-..."           # single key
# or
export OPENAI_API_KEYS="sk-1,sk-2"        # comma separated list
```

If you wish to enable semantic search using Pinecone, add the credentials to
`.streamlit/secrets.toml` as:

```toml
pinecone_api_key = "pc-..."
pinecone_env = "us-east1-gcp"
pinecone_index = "my-index"
```

Alternatively set them as environment variables when running locally:

```bash
export PINECONE_API_KEY="pc-..."
export PINECONE_ENV="us-east1-gcp"
export PINECONE_INDEX="my-index"
```

Open your browser at `http://localhost:8501`, enter a project description
(e.g. "Design a drone for wildfire detection") and click **Run Secure Research**.
A PDF report will be generated for download once the loop completes.

### Running offline

If your environment lacks system packages such as `libpango` required by
WeasyPrint or if the library fails to load, the application automatically
falls back to a pure Python solution using `fpdf` for PDF generation.
Install the Python dependencies from `requirements.txt` using locally available
wheels and run `streamlit run app.py` as described above. No internet connection
is needed at runtime.
