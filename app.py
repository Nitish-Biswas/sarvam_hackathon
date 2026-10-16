from __future__ import annotations

import os
import tempfile
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from heritage_storytelling import (
    LANGUAGES,
    LANGUAGES_BY_CODE,
    OUTPUT_FORMATS,
    TTS_LANGUAGES,
    HeritageStorytellingService,
    ServiceError,
)

load_dotenv()


st.set_page_config(
    page_title="Aaroh · Heritage Storytelling",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');
    :root { --ink:#202d29; --muted:#66716b; --paper:#f4f1e9; --card:#fffdf8; --line:#e2ddd1; --accent:#bb5a38; --green:#315b4a; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
    .stApp { background:var(--paper); }
    [data-testid="stSidebar"] { background:#eae6da; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 { font-family:'Playfair Display',serif; }
    h1,h2,h3 { font-family:'Playfair Display',serif !important; letter-spacing:-.02em; }
    .hero { padding:2rem 2.2rem; border-radius:18px; background:#24463b; color:#f8f4e9; margin:0 0 1.5rem 0; position:relative; overflow:hidden; }
    .hero:after { content:'◈'; position:absolute; right:2rem; top:-2.4rem; font-size:11rem; color:rgba(245,231,194,.09); }
    .eyebrow { text-transform:uppercase; letter-spacing:.18em; font-family:'DM Mono',monospace; font-size:.72rem; color:#e5bd8c; }
    .hero h1 { color:#fff9ed; font-size:3rem; margin:.25rem 0; }
    .hero p { color:#d7e0d8; max-width:650px; margin:0; font-size:1rem; }
    .step-card { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:1.2rem 1.35rem; margin-bottom:.8rem; }
    .step-label { color:var(--accent); font-family:'DM Mono',monospace; font-size:.72rem; letter-spacing:.12em; text-transform:uppercase; }
    .source-note { color:var(--muted); font-size:.84rem; }
    div.stButton > button[kind="primary"] { background:var(--accent); border:0; border-radius:9px; color:white; font-weight:700; padding:.7rem 1.2rem; }
    div.stButton > button[kind="primary"]:hover { background:#98442c; border:0; }
    .stTextArea textarea { background:#fffdf8; }
    [data-testid="stMetric"] { background:#fffdf8; border:1px solid var(--line); border-radius:12px; padding:1rem; }
    footer { visibility:hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def client_or_error() -> HeritageStorytellingService | None:
    key = os.getenv("SARVAM_API_KEY", "").strip()
    if not key:
        st.error("Add your Sarvam key as `SARVAM_API_KEY` in your local environment, then restart the app.")
        st.code('export SARVAM_API_KEY="your-key"\nstreamlit run app.py', language="bash")
        return None
    return HeritageStorytellingService(key)


def delete_temp(path: str | None) -> None:
    if path:
        try:
            Path(path).unlink(missing_ok=True)
        except OSError:
            pass


st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">Oral archives · Manuscripts · Living memory</div>
      <h1>Aaroh</h1>
      <p>Bring heritage into the present. Turn a voice recording or scanned manuscript into a story, podcast, or guided tour with natural multilingual narration.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## ◈ Aaroh")
    st.caption("Heritage Storytelling Agent · Idea library #26")
    st.markdown("---")
    st.markdown("**A simple archive-to-audio journey**")
    st.markdown("1. Bring an oral archive, manuscript, or transcript")
    st.markdown("2. Shape it into a story, podcast, or guided tour")
    st.markdown("3. Translate and listen in a chosen language")
    st.markdown("---")
    st.caption("Your source is processed for this session. The app does not save uploads to a project folder.")

input_col, setting_col = st.columns([1.12, .88], gap="large")

with input_col:
    st.markdown('<div class="step-card"><div class="step-label">01 · Bring an archive</div>', unsafe_allow_html=True)
    source_mode = st.radio(
        "Choose a source",
        ["Oral archive", "Manuscript scan", "Existing transcript"],
        horizontal=True,
        label_visibility="collapsed",
    )
    source_file = None
    source_text = ""
    source_language = "Auto detect"
    if source_mode == "Oral archive":
        source_file = st.file_uploader("Audio recording", type=["wav", "mp3", "m4a", "mp4", "aac", "flac", "ogg", "webm"], help="Saaras handles supported Indic languages and English. Longer recordings are split into short transcription segments.")
        source_language = st.selectbox("Recording language (for best results)", ["Auto detect", *LANGUAGES.keys()], index=0)
    elif source_mode == "Manuscript scan":
        source_file = st.file_uploader("Scanned manuscript", type=["pdf", "png", "jpg", "jpeg", "zip"], help="Document AI digitizes PDFs and scans. PDF/ZIP inputs support up to 10 pages per upload.")
        source_language = st.selectbox("Manuscript language", LANGUAGES.keys(), index=list(LANGUAGES.keys()).index("English"))
    else:
        source_text = st.text_area("Paste an archive transcript or transcription", height=215, placeholder="Paste a family oral history, archival passage, or transcript here…")
        source_language = st.selectbox("Source language", LANGUAGES.keys(), index=list(LANGUAGES.keys()).index("English"))
    st.markdown("</div>", unsafe_allow_html=True)

with setting_col:
    st.markdown('<div class="step-card"><div class="step-label">02 · Choose its next form</div>', unsafe_allow_html=True)
    output_kind = st.radio("Story format", list(OUTPUT_FORMATS.keys()), horizontal=True)
    audience = st.selectbox("Who is it for?", ["A curious general audience", "Families and children", "Visitors at a heritage site", "Students and educators"])
    target_language_name = st.selectbox("Narration language", list(TTS_LANGUAGES.keys()), index=list(TTS_LANGUAGES.keys()).index("Hindi"))
    voice = st.selectbox("Narrator voice", ["shubh", "ritu", "aditya", "priya", "neha", "rahul", "pooja", "rohan", "simran", "kavya"])
    st.markdown('<p class="source-note">The narration is generated in the selected language. The source archive remains available alongside the adaptation.</p>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

run = st.button("Create the heritage experience", type="primary", use_container_width=True)

if run:
    service = client_or_error()
    if service:
        if source_mode != "Existing transcript" and source_file is None:
            st.warning("Add a source file to continue.")
        elif source_mode == "Existing transcript" and not source_text.strip():
            st.warning("Paste a transcript to continue.")
        else:
            progress = st.status("Preparing your archive…", expanded=True)
            audio_path: str | None = None
            try:
                if source_mode == "Oral archive":
                    ext = Path(source_file.name).suffix or ".wav"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp:
                        temp.write(source_file.getvalue())
                        audio_path = temp.name
                    progress.write("Listening to the oral archive with Saaras…")
                    requested_language = None if source_language == "Auto detect" else LANGUAGES[source_language]
                    transcript, detected_language = service.transcribe_audio(
                        audio_path,
                        source_file.name,
                        requested_language,
                    )
                    source_text = transcript
                    source_language = LANGUAGES_BY_CODE.get(detected_language, source_language if source_language != "Auto detect" else "English") if detected_language else (source_language if source_language != "Auto detect" else "English")
                elif source_mode == "Manuscript scan":
                    progress.write("Reading the manuscript with Sarvam Document AI…")
                    source_text = service.digitise_document(
                        source_file.getvalue(),
                        source_file.name,
                        source_file.type or "application/octet-stream",
                        LANGUAGES[source_language],
                    )
                progress.write("Shaping the archive into a new format…")
                shaped = service.create_experience(source_text, OUTPUT_FORMATS[output_kind], audience)
                progress.write(f"Translating into {target_language_name}…")
                translated = service.translate_text(
                    shaped,
                    LANGUAGES[source_language],
                    LANGUAGES[target_language_name],
                )
                progress.write("Recording natural narration with Bulbul…")
                narration = service.synthesize(translated, LANGUAGES[target_language_name], voice)
                st.session_state["heritage_result"] = {
                    "source_mode": source_mode,
                    "source_text": source_text,
                    "shaped": shaped,
                    "translated": translated,
                    "narration": narration,
                    "format": output_kind,
                    "language": target_language_name,
                }
                progress.update(label="Your heritage experience is ready", state="complete", expanded=False)
            except ServiceError as exc:
                progress.update(label="We couldn't finish this archive", state="error", expanded=True)
                st.error(str(exc))
            except Exception as exc:
                progress.update(label="We couldn't finish this archive", state="error", expanded=True)
                st.error(f"Something went wrong while creating the experience: {exc}")
            finally:
                delete_temp(audio_path)

result = st.session_state.get("heritage_result")
if result:
    st.markdown("---")
    st.markdown(f"## Your {result['format'].lower()} is ready")
    st.caption(f"Narrated in {result['language']} · Created from {result['source_mode'].lower()}")
    left, right = st.columns([1.05, .95], gap="large")
    with left:
        st.markdown("### The story")
        st.markdown(result["translated"])
        st.download_button(
            "Download story script (TXT)",
            data=result["translated"].encode("utf-8"),
            file_name="aaroh-heritage-script.txt",
            mime="text/plain; charset=utf-8",
            use_container_width=True,
        )
        st.download_button("Download narration (WAV)", data=result["narration"], file_name="aaroh-heritage-narration.wav", mime="audio/wav", use_container_width=True)
        st.audio(result["narration"], format="audio/wav")
    with right:
        st.markdown("### Archive source")
        with st.expander("View the source text", expanded=False):
            st.text(result["source_text"])
        st.markdown("### Adaptation")
        st.markdown(result["shaped"])

