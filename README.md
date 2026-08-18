# 📝 Video to Notes

Turn any YouTube video into structured, downloadable study notes — automatically.

Paste a link, get back a **summary**, **key term definitions**, and **highlighted takeaways** as a clean PDF, generated end-to-end by an LLM pipeline.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-ff4b4b)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange)

---

## What it does

1. You paste a YouTube video URL
2. The video's transcript is fetched automatically
3. An LLM (Groq / Llama 3.3) reads the transcript and returns structured notes as JSON — not free-text chat output
4. The notes are rendered into a polished, downloadable PDF

No manual copy-pasting into a chatbot, no reformatting — one input, one file out.

## Why this exists

Reviewing long-form video content (lectures, talks, tutorials) is slow — you either rewatch or skim and miss things. This automates the "watch and take notes" step into a repeatable pipeline instead of a manual chat session.

## Architecture

```
YouTube URL
    │
    ▼
[ youtube-transcript-api ]  →  raw transcript text
    │
    ▼
[ Groq API — Llama 3.3 70B ]  →  structured JSON
    │                              { summary, key_terms, takeaways }
    ▼
[ reportlab ]  →  formatted PDF
    │
    ▼
Streamlit UI  →  download button
```

## Tech stack

| Layer | Tool | Why |
|---|---|---|
| Transcript fetch | [`youtube-transcript-api`](https://github.com/jdepoix/youtube-transcript-api) | Pulls captions directly from YouTube, no API key or auth required |
| LLM summarization | **Groq API** (Llama 3.3 70B) | Fast inference; uses Groq's native `response_format={"type": "json_object"}` to force valid structured output at the API level, rather than just prompting for JSON |
| PDF generation | [`reportlab`](https://www.reportlab.com/) | Pure-Python flowable-based layout — builds the document as a stream of styled sections, no manual coordinate math |
| UI | [`streamlit`](https://streamlit.io/) | Turns the pipeline into a usable web app with minimal frontend code |
| Hosting | **Streamlit Community Cloud** | Free, GitHub-connected deployment with built-in secrets management |

## Getting started

```bash
git clone <this-repo-url>
cd video-to-notes
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# then edit .streamlit/secrets.toml and paste your real GROQ_API_KEY
# (get a free key at https://console.groq.com — no card required)

streamlit run app.py
```

The app opens at `http://localhost:8501`. No key saved locally? Just paste it into the sidebar field when the app loads instead.

## Deploying it yourself

1. Push this repo to GitHub (the `.gitignore` already keeps your real key out of it).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select the repo → set the main file to `app.py`.
3. Under **App settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
4. Deploy. Streamlit Cloud installs `requirements.txt` and boots the app automatically.

## Known limitation

`youtube-transcript-api` talks to YouTube directly and unauthenticated, so it can get rate-limited on shared cloud IP ranges (the kind Streamlit Cloud uses) under heavy request volume — even when the same code works fine locally. The fix is routing those specific requests through a residential proxy (e.g. [Webshare](https://www.webshare.io/)); the app's sidebar already has fields ready for proxy credentials once that's wired in.

## Project structure

```
.
├── app.py                          # entire pipeline + Streamlit UI
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example        # template — copy to secrets.toml locally
└── .gitignore                      # keeps secrets.toml and generated PDFs out of git
```
