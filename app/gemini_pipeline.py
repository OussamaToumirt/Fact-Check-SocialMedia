from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Tuple

import google.generativeai as genai

from .config import settings
from .prompts import FACTCHECK_SYSTEM_PROMPT, build_factcheck_user_prompt
from .schemas import FactCheckReport


class GeminiError(RuntimeError):
    pass


def _configure_gemini(api_key: Optional[str] = None):
    """Configure Gemini API with the API key from settings or user-provided key."""
    key = api_key or settings.gemini_api_key
    if key:
        genai.configure(api_key=key)


def transcribe_audio_mp3(mp3_path: Path, api_key: Optional[str] = None) -> str:
    """Transcribe an MP3 audio file using Gemini's audio capabilities."""
    _configure_gemini(api_key)
    
    # Upload the audio file
    audio_file = genai.upload_file(path=str(mp3_path))
    
    # Use Gemini model for transcription
    model = genai.GenerativeModel(settings.transcribe_model)
    
    # Generate transcription
    response = model.generate_content([
        "Please transcribe the following audio file accurately. Provide only the transcription without any additional commentary.",
        audio_file
    ])
    
    return response.text


def fact_check_transcript(
    *, transcript: str, url: Optional[str] = None, output_language: str = "ar", api_key: Optional[str] = None
) -> Tuple[FactCheckReport, dict[str, Any]]:
    """
    Perform fact-checking on the transcript using Gemini.
    Returns (report, raw_response_dict).
    """
    _configure_gemini(api_key)
    
    # Get the JSON schema for the response format
    schema = FactCheckReport.model_json_schema()
    
    # Build the prompt
    user_prompt = build_factcheck_user_prompt(
        transcript=transcript, 
        url=url, 
        output_language=output_language
    )
    
    # Configure the model with grounding (web search)
    model = genai.GenerativeModel(
        settings.factcheck_model,
        tools='google_search_retrieval',
    )
    
    # Create the full prompt with system instructions
    full_prompt = f"{FACTCHECK_SYSTEM_PROMPT}\n\n{user_prompt}\n\nPlease respond with a valid JSON object matching this schema:\n{json.dumps(schema, indent=2)}"
    
    # Generate the response
    try:
        response = model.generate_content(
            full_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                response_mime_type="application/json",
            )
        )
        
        output_text = response.text
        if not output_text:
            raise GeminiError("Empty model output.")
        
        # Parse the JSON response
        try:
            report_dict = json.loads(output_text)
        except json.JSONDecodeError as e:
            raise GeminiError(f"Model did not return valid JSON: {e}") from e
        
        # Add timestamp if not present
        if "generated_at" not in report_dict:
            report_dict["generated_at"] = datetime.now(tz=timezone.utc).isoformat()
        
        # Validate against the schema
        report = FactCheckReport.model_validate(report_dict)
        
        # Build raw response data
        raw = {
            "model": settings.factcheck_model,
            "output_text": output_text,
            "finish_reason": response.candidates[0].finish_reason if response.candidates else None,
            "usage_metadata": {
                "prompt_token_count": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "candidates_token_count": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
                "total_token_count": response.usage_metadata.total_token_count if response.usage_metadata else 0,
            } if response.usage_metadata else {},
            "grounding_metadata": response.candidates[0].grounding_metadata if response.candidates and hasattr(response.candidates[0], 'grounding_metadata') else None,
        }
        
        return report, raw
        
    except Exception as e:
        if isinstance(e, GeminiError):
            raise
        raise GeminiError(f"Error calling Gemini API: {e}") from e
