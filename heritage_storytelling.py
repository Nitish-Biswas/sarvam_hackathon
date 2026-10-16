from __future__ import annotations

import base64
import io
import re
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Iterable

import requests
from pydub import AudioSegment
from sarvamai import SarvamAI


LANGUAGES = {
    "Assamese": "as-IN",
    "Bengali": "bn-IN",
    "English": "en-IN",
    "Gujarati": "gu-IN",
    "Hindi": "hi-IN",
    "Kannada": "kn-IN",
    "Kashmiri": "ks-IN",
    "Konkani": "kok-IN",
    "Malayalam": "ml-IN",
    "Manipuri": "mni-IN",
    "Marathi": "mr-IN",
    "Nepali": "ne-IN",
    "Odia": "od-IN",
    "Punjabi": "pa-IN",
    "Sanskrit": "sa-IN",
    "Sindhi": "sd-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Urdu": "ur-IN",
}
LANGUAGES_BY_CODE = {code: name for name, code in LANGUAGES.items()}
LANGUAGES_BY_CODE.update({"en-US": "English", "en-GB": "English"})
TTS_LANGUAGES = {
    name: LANGUAGES[name]
    for name in (
        "Bengali",
        "English",
        "Gujarati",
        "Hindi",
        "Kannada",
        "Malayalam",
        "Marathi",
        "Odia",
        "Punjabi",
        "Tamil",
        "Telugu",
    )
}

OUTPUT_FORMATS = {
    "Interactive story": "interactive story",
    "Podcast episode": "podcast episode script",
    "Guided tour": "guided tour",
}


class ServiceError(Exception):
    """An actionable, user-facing error from an archive processing step."""


def _chunks(text: str, limit: int) -> list[str]:
    """Split text on sentence boundaries, then words, without dropping content."""
    clean = re.sub(r"\s+", " ", text).strip()
    if len(clean) <= limit:
        return [clean] if clean else []
    sentences = re.split(r"(?<=[.!?।])\s+", clean)
    result: list[str] = []
    current = ""
    for sentence in sentences:
        if len(sentence) > limit:
            words = sentence.split()
            for word in words:
                if len(word) > limit:
                    raise ServiceError("A single word in this archive is too long to process safely.")
                if current and len(current) + len(word) + 1 > limit:
                    result.append(current)
                    current = ""
                current = f"{current} {word}".strip()
            continue
        if current and len(current) + len(sentence) + 1 > limit:
            result.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        result.append(current)
    return result


def _wav_chunks(audio: AudioSegment, milliseconds: int = 25_000) -> Iterable[bytes]:
    for offset in range(0, len(audio), milliseconds):
        part = audio[offset : offset + milliseconds]
        part = part.set_frame_rate(16_000).set_channels(1).set_sample_width(2)
        output = io.BytesIO()
        part.export(output, format="wav")
        yield output.getvalue()


class HeritageStorytellingService:
    def __init__(self, api_key: str):
        try:
            self.client = SarvamAI(api_subscription_key=api_key)
        except Exception as exc:
            raise ServiceError(f"Could not initialize the Sarvam client: {exc}") from exc

    def transcribe_audio(self, path: str, original_name: str, language_code: str | None = None) -> tuple[str, str | None]:
        try:
            audio = AudioSegment.from_file(path)
            if len(audio) == 0:
                raise ServiceError("The audio file is empty.")
            transcripts: list[str] = []
            detected_languages: list[str] = []
            for chunk in _wav_chunks(audio):
                with tempfile.NamedTemporaryFile(suffix=".wav") as audio_file:
                    audio_file.write(chunk)
                    audio_file.flush()
                    with open(audio_file.name, "rb") as stream:
                        response = self.client.speech_to_text.transcribe(
                            file=(f"{Path(original_name).stem}.wav", stream),
                            model="saaras:v4",
                            mode="transcribe",
                            language_code=language_code,
                        )
                transcript = getattr(response, "transcript", "") or ""
                if transcript.strip():
                    transcripts.append(transcript.strip())
                language = getattr(response, "language_code", None)
                if language:
                    detected_languages.append(language)
            if not transcripts:
                raise ServiceError("Saaras did not return any transcript. Try a clearer audio recording.")
            detected = max(set(detected_languages), key=detected_languages.count) if detected_languages else None
            return "\n\n".join(transcripts), detected
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"Audio transcription failed. Check that FFmpeg is installed and the file is a supported audio format. Details: {exc}") from exc

    def digitise_document(self, data: bytes, filename: str, mime_type: str, language: str) -> str:
        supported = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".zip": "application/zip"}
        extension = Path(filename).suffix.lower()
        if extension not in supported:
            raise ServiceError("Use a PDF, PNG, JPG, JPEG, or ZIP scan of the manuscript.")
        if not data:
            raise ServiceError("The manuscript file is empty.")
        if len(data) > 200 * 1024 * 1024:
            raise ServiceError("This manuscript is larger than the 200 MB Document AI limit.")
        try:
            job = self.client.doc_ai.digitise(
                file=[(Path(filename).name, io.BytesIO(data), supported[extension])],
                language=language,
                content_type="mixed",
            )
            terminal_states = {"completed", "partially_completed", "failed", "rejected"}
            status = str(getattr(job, "status", "pending")).lower()
            deadline = time.monotonic() + 300
            while status not in terminal_states:
                if time.monotonic() >= deadline:
                    raise ServiceError("Manuscript digitization is taking longer than expected. Please try again shortly.")
                time.sleep(3)
                job = self.client.doc_ai.get_status(job_id=job.job_id)
                status = str(getattr(job, "status", "")).lower()
            if status not in {"completed", "partially_completed"}:
                raise ServiceError(f"Document AI could not digitize this manuscript (status: {status}).")
            download = self.client.doc_ai.get_download_url(job_id=job.job_id)
            response = requests.request(download.method, download.url, headers=download.headers or {}, timeout=90)
            response.raise_for_status()
            return self._extract_markdown(response.content)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"Manuscript digitization failed. Check the scan quality and language setting. Details: {exc}") from exc

    @staticmethod
    def _extract_markdown(payload: bytes) -> str:
        if not zipfile.is_zipfile(io.BytesIO(payload)):
            text = payload.decode("utf-8", errors="replace").strip()
            if not text:
                raise ServiceError("Document AI returned an empty manuscript transcription.")
            return text
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            candidates = [name for name in archive.namelist() if name.lower().endswith(".md") and "/metadata/" not in name.lower()]
            if not candidates:
                candidates = [name for name in archive.namelist() if name.lower().endswith((".txt", ".html")) and "/metadata/" not in name.lower()]
            if not candidates:
                raise ServiceError("Document AI completed, but its result archive contained no readable text file.")
            contents = [archive.read(name).decode("utf-8", errors="replace").strip() for name in sorted(candidates)]
            text = "\n\n".join(part for part in contents if part)
            if not text:
                raise ServiceError("Document AI returned an empty manuscript transcription.")
            return text

    def create_experience(self, source_text: str, format_name: str, audience: str) -> str:
        source = source_text.strip()
        if not source:
            raise ServiceError("There is no archive text to transform.")
        if len(source) > 60_000:
            raise ServiceError("This source is too long for one story generation. Use a shorter excerpt (up to about 60,000 characters).")
        prompt = f"""Transform the supplied heritage archive into a {format_name} for {audience}.

Requirements:
- Keep the account grounded in the supplied source. Do not add historical facts, dates, names, events, quotations, or claims that are not present in it.
- Preserve the source's people, places, sequence, and meaning. Where a detail is unclear, retain the uncertainty instead of guessing.
- Make the result engaging and easy to follow when read aloud.
- For an interactive story, include a few natural reader choices or reflection prompts without inventing alternate historical events.
- For a podcast episode script, write a narrator-led episode with a title, opening, clear sections, and a closing. Do not invent interviewees or quotes.
- For a guided tour, organize the script into stops with a short spoken introduction at each stop. Do not imply a place exists unless the source says so.
- Return only the finished script in the same language as the source.

ARCHIVE SOURCE:
{source}
"""
        try:
            response = self.client.chat.completions(
                model="sarvam-105b",
                messages=[
                    {"role": "system", "content": "You are an editor for a public heritage archive. Preserve source meaning and never fabricate historical details."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.35,
                max_tokens=5000,
            )
            result = response.choices[0].message.content.strip()
            if not result:
                raise ServiceError("The story service returned an empty script.")
            return result
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(f"Could not shape the archive into a {format_name}: {exc}") from exc

    def translate_text(self, text: str, source_language: str, target_language: str) -> str:
        if source_language == target_language:
            return text
        parts = _chunks(text, 1800)
        if not parts:
            raise ServiceError("There is no text to translate.")
        try:
            translated: list[str] = []
            for part in parts:
                response = self.client.text.translate(
                    input=part,
                    source_language_code=source_language,
                    target_language_code=target_language,
                    model="sarvam-translate:v1",
                )
                translated.append(response.translated_text.strip())
            return "\n\n".join(translated)
        except Exception as exc:
            raise ServiceError(f"Translation failed. Check the selected source and narration languages. Details: {exc}") from exc

    def synthesize(self, text: str, language: str, speaker: str) -> bytes:
        parts = _chunks(text, 2300)
        if not parts:
            raise ServiceError("There is no narration text to synthesize.")
        segments: list[AudioSegment] = []
        try:
            for part in parts:
                response = self.client.text_to_speech.convert(
                    text=part,
                    model="bulbul:v3",
                    language_code=language,
                    speaker=speaker,
                    output_audio_codec="wav",
                )
                encoded = response.audios[0]
                segments.append(AudioSegment.from_file(io.BytesIO(base64.b64decode(encoded)), format="wav"))
            combined = AudioSegment.empty()
            for segment in segments:
                combined += segment
            output = io.BytesIO()
            combined.export(output, format="wav")
            return output.getvalue()
        except Exception as exc:
            raise ServiceError(f"Narration generation failed. Try a different voice or a shorter script. Details: {exc}") from exc
