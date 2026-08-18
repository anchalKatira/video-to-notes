"""
app.py

Single-video version: paste one YouTube video URL -> fetch its transcript ->
summarize into structured notes with Groq (Llama 3.3) -> download as PDF.

Run locally:
    pip install -r requirements.txt
    export GROQ_API_KEY="gsk_..."
    streamlit run app.py
"""

import json
import os
import re
import tempfile

import streamlit as st
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound, VideoUnavailable

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, HRFlowable
from reportlab.lib import colors


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL = "llama-3.3-70b-versatile"
MAX_TRANSCRIPT_CHARS = 100_000

NOTES_SYSTEM_PROMPT = """You are an expert note-taker. You will be given the \
raw transcript of a single YouTube video. Produce structured study notes from it.

Respond with ONLY a JSON object with this exact shape:

{
  "summary": "A clear 3-6 sentence summary of what the video covers and why it matters.",
  "key_terms": [
    {"term": "Term or concept name", "definition": "One or two sentence plain-language definition."}
  ],
  "takeaways": [
    "A single highlighted, actionable or memorable takeaway.",
    "Another takeaway."
  ]
}

Guidelines:
- key_terms: include 3-8 of the most important terms/concepts actually discussed. Skip if the video has none.
- takeaways: include 3-6 of the most important points, phrased concisely.
- Base everything only on the transcript content. Do not invent facts.
- If the transcript is garbled or very short, do your best and note briefly in the summary that the transcript was limited.
"""


# ---------------------------------------------------------------------------
# Pipeline steps
# ---------------------------------------------------------------------------

def extract_video_id(url: str) -> str:
    """Pulls the 11-char video ID out of any common YouTube URL shape."""
    patterns = [
        r"(?:v=|/)([0-9A-Za-z_-]{11}).*",   # watch?v=... or /embed/...
        r"youtu\.be/([0-9A-Za-z_-]{11})",   # youtu.be short links
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    raise ValueError("Couldn't find a video ID in that URL. Paste a normal YouTube video link.")


def get_transcript_text(video_id: str) -> str:
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id)
    text = " ".join(snippet.text for snippet in fetched)
    if len(text) > MAX_TRANSCRIPT_CHARS:
        text = text[:MAX_TRANSCRIPT_CHARS] + "\n[...transcript truncated for length...]"
    return text


def generate_notes(client: Groq, transcript: str) -> dict:
    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},  # forces valid JSON at the API level
        messages=[
            {"role": "system", "content": NOTES_SYSTEM_PROMPT},
            {"role": "user", "content": f"Transcript:\n{transcript}"},
        ],
    )
    return json.loads(response.choices[0].message.content)


def build_pdf(video_title: str, video_url: str, notes: dict, output_path: str):
    doc = SimpleDocTemplate(
        output_path, pagesize=LETTER,
        topMargin=0.9 * inch, bottomMargin=0.9 * inch,
        leftMargin=0.9 * inch, rightMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=20, spaceAfter=6)
    section_style = ParagraphStyle("Section", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#4a4a68"))
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=11, leading=16, alignment=TA_LEFT)
    meta_style = ParagraphStyle("Meta", parent=styles["Normal"], fontSize=9, textColor=colors.grey, spaceAfter=14)

    story = [
        Paragraph(video_title, title_style),
        Paragraph(f'<link href="{video_url}">{video_url}</link>', meta_style),
        HRFlowable(width="100%", color=colors.HexColor("#dddddd")),
        Spacer(1, 10),
        Paragraph("Summary", section_style),
        Paragraph(notes.get("summary", ""), body_style),
    ]

    key_terms = notes.get("key_terms", [])
    if key_terms:
        story.append(Paragraph("Key Terms", section_style))
        items = [ListItem(Paragraph(f"<b>{kt.get('term','')}</b> — {kt.get('definition','')}", body_style)) for kt in key_terms]
        story.append(ListFlowable(items, bulletType="bullet", leftIndent=16))

    takeaways = notes.get("takeaways", [])
    if takeaways:
        story.append(Paragraph("Highlighted Takeaways", section_style))
        items = [ListItem(Paragraph(t, body_style)) for t in takeaways]
        story.append(ListFlowable(items, bulletType="bullet", leftIndent=16))

    doc.build(story)


# ---------------------------------------------------------------------------
# Streamlit UI
# ---------------------------------------------------------------------------

st.set_page_config(page_title="Video to Notes", page_icon="📝", layout="centered")
st.title("📝 YouTube Video → Notes PDF")
st.caption("Paste one video link. Get back a summary, key terms, and takeaways as a PDF.")

default_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""
with st.sidebar:
    st.header("Settings")
    api_key = st.text_input("Groq API key", value=default_key, type="password")

video_url = st.text_input("YouTube video URL", placeholder="https://www.youtube.com/watch?v=...")
run_button = st.button("Generate notes", type="primary", disabled=not (video_url and api_key))

if not api_key:
    st.info("Enter your Groq API key in the sidebar to get started.")

if run_button:
    try:
        with st.spinner("Fetching transcript..."):
            video_id = extract_video_id(video_url)
            transcript = get_transcript_text(video_id)

        with st.spinner("Generating notes with Groq..."):
            client = Groq(api_key=api_key)
            notes = generate_notes(client, transcript)

        with st.spinner("Building PDF..."):
            video_title = f"Notes: {video_id}"  # no title lookup in the single-video version
            video_page_url = f"https://www.youtube.com/watch?v={video_id}"
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                build_pdf(video_title, video_page_url, notes, tmp.name)
                with open(tmp.name, "rb") as f:
                    pdf_bytes = f.read()
                os.unlink(tmp.name)

        st.success("Done!")
        st.download_button("⬇️ Download PDF", data=pdf_bytes, file_name="video_notes.pdf", mime="application/pdf")

        with st.expander("Preview"):
            st.write(notes.get("summary", ""))
            if notes.get("key_terms"):
                st.markdown("**Key terms**")
                for kt in notes["key_terms"]:
                    st.markdown(f"- **{kt.get('term','')}** — {kt.get('definition','')}")
            if notes.get("takeaways"):
                st.markdown("**Takeaways**")
                for t in notes["takeaways"]:
                    st.markdown(f"- {t}")

    except (TranscriptsDisabled, NoTranscriptFound):
        st.error("This video has no captions/transcript available.")
    except VideoUnavailable:
        st.error("That video is unavailable.")
    except ValueError as e:
        st.error(str(e))
    except json.JSONDecodeError:
        st.error("The model's response couldn't be parsed. Try again.")
    except Exception as e:
        st.error(f"Something went wrong: {e}")
