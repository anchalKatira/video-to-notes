# 📝 Video to Notes

Turn any YouTube video into structured, downloadable study notes — automatically.

Paste a link, get back a **summary**, **key term definitions**, and **highlighted takeaways** as a clean PDF — generated end-to-end by an LLM pipeline. No manual copy-pasting into a chatbot, no reformatting: one input, one file out.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-app-ff4b4b)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange)
![License](https://img.shields.io/badge/license-MIT-green)

🔗 **Live demo:** [video-to-notes.streamlit.app](https://video-to-notes.streamlit.app) <!-- replace with your actual deployed URL once live -->

---

## Table of contents

- [Demo](#demo)
- [Why this exists](#why-this-exists)
- [Features](#features)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Getting started](#getting-started)
- [Deploying it yourself](#deploying-it-yourself)
- [Project structure](#project-structure)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)
- [Author](#author)

## Demo

<!-- Add a screenshot or short GIF of the app here once deployed, e.g.: -->
<!-- ![App screenshot](docs/screenshot.png) -->

Paste a YouTube link → click **Generate notes** → download a formatted PDF in seconds.

## Why this exists

Reviewing long-form video content (lectures, talks, tutorials) is slow — you either rewatch or skim and miss things. This automates the "watch and take notes" step into a repeatable pipeline instead of a manual chat session with an AI assistant, and produces a real file you can keep, print, or share.

## Features

- 🔗 Works with any public YouTube video that has captions (manual or auto-generated)
- 🧠 LLM-generated structured notes — not free-text chat output, but a consistent, parseable format every time
- 📄 Clean, styled PDF output (summary, key terms, highlighted takeaways)
- ⚡ Fast inference via Groq's LPU-based API
- 🔒 API key handled via Streamlit secrets — never hardcoded or committed
- 🖥️ Simple one-page UI, no setup needed for end users

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
git clone https://github.com/anchalKatira/video-to-notes.git
cd video-to-notes
pip install -r requirements.txt

cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edit .streamlit/secrets.toml and paste your real GROQ_API_KEY
# (get a free key at https://console.groq.com — no card required)

streamlit run app.py
```

The app opens at `http://localhost:8501`. No key saved locally? Just paste it into the sidebar field when the app loads instead.

## Deploying it yourself

1. Push this repo to GitHub (`.gitignore` already keeps your real key out of it).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → select the repo → set the main file to `app.py`.
3. Under **App settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_..."
   ```
4. Deploy. Streamlit Cloud installs `requirements.txt` and boots the app automatically.

## Project structure

```
.
├── app.py                          # entire pipeline + Streamlit UI
├── requirements.txt
├── .streamlit/
│   └── secrets.toml.example        # template — copy to secrets.toml locally
├── .gitignore                      # keeps secrets.toml and generated PDFs out of git
└── README.md
```

## Known limitations

- **Cloud IP rate-limiting:** `youtube-transcript-api` talks to YouTube directly and unauthenticated, so it can get rate-limited on shared cloud IP ranges (like Streamlit Cloud's) under heavy request volume, even when the same code works fine locally. Fix: route those requests through a residential proxy (e.g. [Webshare](https://www.webshare.io/)) — the sidebar already has fields ready for those credentials.
- **Captions required:** videos with no captions at all (manual or auto-generated) can't be processed.
- **Single video at a time:** no batch/playlist support in this version — built as a focused, defensible single-purpose tool.

## Roadmap

- [ ] Wire in Webshare proxy support to eliminate the IP rate-limit risk
- [ ] Add exponential backoff/retry on transient API failures
- [ ] Playlist mode (batch-process every video in a playlist into one combined PDF)
- [ ] Cache results in session state so re-rendering the PDF doesn't require re-calling the LLM

## Author

**Anchal Katira** — B.Tech CSE (AI & ML), VIT Bhopal
[GitHub](https://github.com/anchalKatira)
