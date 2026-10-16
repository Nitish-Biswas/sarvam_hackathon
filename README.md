# Aaroh — Heritage Storytelling Agent

Aaroh implements **idea #26 from the supplied idea library: Heritage Storytelling Agent**. It turns oral archives and historic manuscripts into interactive stories, podcast scripts, or guided tours, then translates and narrates them in an Indian language.

## Archive-to-story flow

1. **Bring an archive:** upload an audio recording, scan/PDF manuscript, or paste an existing transcript.
2. **Shape the material:** choose an interactive story, podcast episode, or guided tour for the intended audience.
3. **Listen in another language:** translate the script and generate natural narration.

Audio archives are transcribed with Saaras. Scanned manuscripts are digitized with Sarvam Document AI. Sarvam-105B shapes the source into the selected format, Sarvam Translate translates it, and Bulbul creates the narration. The source and adapted script remain visible together.

## Run locally

Requires Python 3.10+ and FFmpeg.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
export SARVAM_API_KEY="your-sarvam-key"
streamlit run app.py
```

On macOS, install FFmpeg with `brew install ffmpeg`. On Ubuntu/Debian, use `sudo apt-get install ffmpeg`.

The key is read from `SARVAM_API_KEY` in your shell or a local `.env` file. `.env` is Git-ignored; `.env.example` is only an empty template. Do not paste the key into source files or commit it. The app does not save uploads to the repository. Sarvam API calls send the selected source material to Sarvam for processing; consult the Sarvam data-retention settings that apply to your account before uploading sensitive archive content.

## Run in Docker

```bash
docker build -t aaroh .
docker run --rm -p 8501:8501 -e SARVAM_API_KEY="$SARVAM_API_KEY" aaroh
```

The image runs as a non-root user and includes FFmpeg plus a Streamlit health check. Supply the key at runtime; it is not part of the image.

## Inputs and limits

- Audio: WAV, MP3, M4A, MP4, AAC, FLAC, OGG, or WebM. Audio is divided into 25-second chunks to fit the synchronous Saaras transcription API.
- Manuscripts: PDF, PNG, JPG/JPEG, or a ZIP of page images. Sarvam Document AI supports up to 10 pages per PDF/ZIP job and 200 MB per file.
- Existing text: paste a transcript or digitized passage directly.
- Narration: Bengali, English, Gujarati, Hindi, Kannada, Malayalam, Marathi, Odia, Punjabi, Tamil, or Telugu.

## Provided AudioRefine source

The supplied `AudioRefine-main 2/` folder is preserved as received. Aaroh uses its video/audio-processing foundation as reference while implementing the heritage archive workflow; it does not overwrite those files.
