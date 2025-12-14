# Fact-Check Reels
End-to-end platform to fact-check Instagram Reels audio:
1) download audio via `yt-dlp` → 2) transcribe with `gpt-4o-transcribe` → 3) fact-check with `gpt-5.2-2025-12-11` + web search.

## Security note (important)
If you pasted an OpenAI API key into chat, assume it is compromised and **rotate it immediately** in the OpenAI dashboard.

## Prereqs
- Python 3.10+
- `ffmpeg` (required by `yt-dlp` for MP3 extraction)
  - macOS: `brew install ffmpeg`

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Run
```bash
uvicorn app.main:app --reload
```
Open `http://127.0.0.1:8000`.

## Features
- Output language selector (Arabic/English/French + more)
- Saved results per URL+language (submit the same URL again to reuse the last report)
- Optional re-run to overwrite the saved report

## Docker
```bash
export OPENAI_API_KEY=...
docker compose up --build
```

## Notes
- Downloading content may be restricted by Instagram and/or violate terms for certain URLs. Use only content you have rights to access.
- For some reels you may need cookies (`YTDLP_COOKIES_FILE`).
