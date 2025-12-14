from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Tuple

from openai import OpenAI

from .config import settings
from .prompts import FACTCHECK_SYSTEM_PROMPT, build_factcheck_user_prompt
from .schemas import FactCheckReport


class OpenAIError(RuntimeError):
    pass


def _client(api_key: Optional[str] = None, base_url: Optional[str] = None) -> OpenAI:
    return OpenAI(
        api_key=api_key or settings.openai_api_key,
        base_url=base_url
    )


def transcribe_audio_mp3(mp3_path: Path, api_key: Optional[str] = None, base_url: Optional[str] = None, model: Optional[str] = None) -> str:
    client = _client(api_key, base_url)
    model = model or settings.openai_model # Fallback, though usually whisper-1
    
    # OpenAI usually uses 'whisper-1' for transcription
    transcribe_model = "whisper-1" 
    
    with mp3_path.open("rb") as f:
        tx = client.audio.transcriptions.create(
            model=transcribe_model,
            file=f,
            response_format="text",
        )
    
    if isinstance(tx, str):
        return tx
    return getattr(tx, "text", "") or ""


def fact_check_transcript(
    *, 
    transcript: str, 
    url: Optional[str] = None, 
    output_language: str = "ar",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model: Optional[str] = None
) -> Tuple[FactCheckReport, dict[str, Any]]:
    
    client = _client(api_key, base_url)
    model = model or settings.openai_model
    
    schema = FactCheckReport.model_json_schema()
    
    # Add schema to prompt for models that don't support strict json_schema
    system_prompt = f"{FACTCHECK_SYSTEM_PROMPT}\n\nYou must respond with a valid JSON object matching this schema:\n{json.dumps(schema, indent=2)}"
    
    user_prompt = build_factcheck_user_prompt(transcript=transcript, url=url, output_language=output_language)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
    except Exception as e:
        raise OpenAIError(f"OpenAI API error: {e}") from e

    output_text = response.choices[0].message.content or ""
    if not output_text:
        raise OpenAIError("Empty model output.")

    try:
        report_dict = json.loads(output_text)
    except json.JSONDecodeError as e:
        raise OpenAIError(f"Model did not return valid JSON: {e}") from e

    if "generated_at" not in report_dict:
        report_dict["generated_at"] = datetime.now(tz=timezone.utc).isoformat()

    try:
        report = FactCheckReport.model_validate(report_dict)
    except Exception as e:
         # Try to be lenient if possible, or just fail
         raise OpenAIError(f"Validation failed: {e}") from e

    raw = response.model_dump(mode="json")
    return report, raw

