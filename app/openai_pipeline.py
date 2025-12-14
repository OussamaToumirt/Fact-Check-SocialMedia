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


def _dereference_json_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    OpenAI structured outputs supports JSON Schema, but some runtimes are finicky about $ref/$defs.
    This helper inlines local "#/$defs/..." references to keep the schema self-contained.
    """
    defs: dict[str, Any] = schema.get("$defs", {}) if isinstance(schema.get("$defs"), dict) else {}
    resolving: set[str] = set()
    resolved_cache: dict[str, Any] = {}

    def resolve_ref(ref: str) -> Any:
        prefix = "#/$defs/"
        if not ref.startswith(prefix):
            return {"$ref": ref}
        name = ref[len(prefix) :]
        if name in resolved_cache:
            return resolved_cache[name]
        if name in resolving:
            # Shouldn't happen for our schema; keep as-is to avoid infinite recursion.
            return defs.get(name, {"$ref": ref})
        resolving.add(name)
        resolved_cache[name] = _walk(defs.get(name, {"$ref": ref}))
        resolving.remove(name)
        return resolved_cache[name]

    def _walk(node: Any) -> Any:
        if isinstance(node, list):
            return [_walk(x) for x in node]
        if not isinstance(node, dict):
            return node
        if "$ref" in node and isinstance(node["$ref"], str):
            return resolve_ref(node["$ref"])
        out: dict[str, Any] = {}
        for k, v in node.items():
            if k == "$defs":
                continue
            out[k] = _walk(v)
        return out

    flattened = _walk(schema)
    if isinstance(flattened, dict):
        flattened.pop("$defs", None)
    return flattened


def _tighten_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Make object schemas explicit about additionalProperties.
    This improves determinism for structured outputs and keeps responses small/consistent.
    """

    def walk(node: Any) -> Any:
        if isinstance(node, list):
            return [walk(x) for x in node]
        if not isinstance(node, dict):
            return node

        is_objectish = node.get("type") == "object" or "properties" in node
        if is_objectish and isinstance(node.get("properties"), dict):
            # OpenAI structured outputs expects required to include every property key.
            props: dict[str, Any] = node["properties"]
            node["required"] = list(props.keys())
            node["additionalProperties"] = False

        for k, v in list(node.items()):
            node[k] = walk(v)
        return node

    return walk(schema)


def _client() -> OpenAI:
    # openai sdk also reads OPENAI_API_KEY from env, but we keep it explicit.
    return OpenAI(api_key=settings.openai_api_key or None)


def transcribe_audio_mp3(mp3_path: Path) -> str:
    client = _client()
    with mp3_path.open("rb") as f:
        tx = client.audio.transcriptions.create(
            model=settings.transcribe_model,
            file=f,
            response_format="text",
        )
    # SDK may return a plain string or an object with `.text`
    if isinstance(tx, str):
        return tx
    return getattr(tx, "text", "") or ""


def fact_check_transcript(
    *, transcript: str, url: Optional[str] = None, output_language: str = "ar"
) -> Tuple[FactCheckReport, dict[str, Any]]:
    """
    Returns (report, raw_response_dict) where raw_response_dict includes tool sources when requested.
    """
    client = _client()

    schema = _tighten_schema(_dereference_json_schema(FactCheckReport.model_json_schema()))

    response = client.responses.create(
        model=settings.factcheck_model,
        input=[
            {"role": "system", "content": FACTCHECK_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": build_factcheck_user_prompt(transcript=transcript, url=url, output_language=output_language),
            },
        ],
        tools=[
            {
                "type": "web_search",
                "user_location": {"type": "approximate"},
                "search_context_size": "medium",
            }
        ],
        reasoning={"effort": "high", "summary": "auto"},
        text={
            "verbosity": "medium",
            "format": {
                "type": "json_schema",
                "name": "fact_check_report",
                "strict": True,
                "schema": schema,
            },
        },
        store=True,
        include=["reasoning.encrypted_content", "web_search_call.action.sources"],
    )

    output_text = getattr(response, "output_text", None) or ""
    if not output_text:
        raise OpenAIError("Empty model output.")

    try:
        report_dict = json.loads(output_text)
    except json.JSONDecodeError as e:
        raise OpenAIError(f"Model did not return valid JSON: {e}") from e

    if "generated_at" not in report_dict:
        report_dict["generated_at"] = datetime.now(tz=timezone.utc).isoformat()

    report = FactCheckReport.model_validate(report_dict)
    raw = response.model_dump(mode="json") if hasattr(response, "model_dump") else {}
    return report, raw
