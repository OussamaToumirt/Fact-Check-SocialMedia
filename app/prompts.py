FACTCHECK_SYSTEM_PROMPT = """\
You are a meticulous, skeptical fact-checker for short-form videos (Instagram Reels/TikTok style).

Goal: Evaluate factual accuracy of statements in the transcript and assess potential harm.

Method:
1) Extract distinct, checkable factual claims (including implied numeric/statistical claims).
2) Use the web_search tool to verify each claim.
3) Decide a per-claim verdict and confidence, then compute an overall verdict + score.
4) Assess danger/harm potential (especially medical/financial/illegal/self-harm/dangerous challenges).

Rules:
- Separate *factual claims* from opinions, jokes, satire, rhetorical questions, or pure anecdotes.
- Prefer primary/authoritative sources (government, academic/peer-reviewed, major institutions, reputable news).
- Never hallucinate sources. Only cite sources you actually found via web_search.
- If evidence is weak/conflicting, say so explicitly and lower confidence.
- If the transcript is ambiguous or likely mistranscribed, call that out in limitations.
- Avoid doxxing or unnecessary personal details; focus on verifying claims, not identifying individuals.
- IMPORTANT: Every field in the JSON schema is required. Never omit keys; use null for unknown strings, 0 for unknown numbers (only when allowed), and [] for empty lists.

Scoring guidance (0-100):
- 90–100: strong evidence most claims correct; minor quibbles only.
- 70–89: mostly correct but some missing context or small errors.
- 40–69: mixed; multiple important issues or cherry-picking.
- 10–39: largely misleading/incorrect.
- 0–9: wholly false or promotes dangerous misinformation.

Overall verdict must be one of:
accurate, mostly_accurate, mixed, misleading, false, unverifiable.

Per-claim verdict must be one of:
supported, contradicted, mixed, unverifiable, not_a_factual_claim.

Danger items:
- category must be one of: medical_misinformation, financial_scam, illegal_instructions, self_harm,
  dangerous_challenge, hate_or_harassment, privacy_or_doxxing, other.
- severity is 0–5 (0 = none, 5 = severe/imminent).
- include a short mitigation suggestion when applicable.

Output must follow the provided JSON schema exactly.
"""


LANGUAGE_NAME_BY_CODE = {
    "ar": "Arabic",
    "bn": "Bengali",
    "cs": "Czech",
    "da": "Danish",
    "en": "English",
    "el": "Greek",
    "fr": "French",
    "es": "Spanish",
    "fa": "Persian",
    "de": "German",
    "fi": "Finnish",
    "he": "Hebrew",
    "hu": "Hungarian",
    "id": "Indonesian",
    "it": "Italian",
    "ms": "Malay",
    "no": "Norwegian",
    "ro": "Romanian",
    "pt": "Portuguese",
    "ru": "Russian",
    "sw": "Swahili",
    "th": "Thai",
    "tl": "Filipino (Tagalog)",
    "zh": "Chinese",
    "ja": "Japanese",
    "ko": "Korean",
    "hi": "Hindi",
    "tr": "Turkish",
    "nl": "Dutch",
    "sv": "Swedish",
    "pl": "Polish",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
}


def build_factcheck_user_prompt(*, transcript: str, url: str | None = None, output_language: str = "ar") -> str:
    lang_code = (output_language or "").strip().lower() or "ar"
    lang_name = LANGUAGE_NAME_BY_CODE.get(lang_code, lang_code)
    meta = f"Video URL: {url}\n\n" if url else ""
    return (
        f"{meta}"
        f"Requested output language: {lang_name} (code: {lang_code}).\n"
        "Write all human-readable text fields (summary, whats_right/wrong, missing_context, claim explanations, corrections, danger descriptions/mitigations, limitations) in that language.\n"
        "Do NOT translate JSON keys or enum values.\n"
        "For sources_used and per-claim sources: keep source titles/publishers as they appear on the source (do not translate).\n\n"
        "Transcript (verbatim, may contain errors):\n"
        f"{transcript}\n\n"
        "Task:\n"
        "1) Extract the distinct factual claims (including implied numeric/statistical claims).\n"
        "2) Verify each claim using web_search.\n"
        "3) Produce an overall accuracy score (0-100) and a plain-language summary of what is right vs wrong.\n"
        "4) Assess danger/harm potential and recommend an on-screen warning if needed.\n"
        "5) Populate sources_used with the unique sources you relied on (deduplicate URLs).\n"
    )
