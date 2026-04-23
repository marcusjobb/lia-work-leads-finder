import json
import re

import llm_client


class LanguageValidationResult:
    def __init__(self, ok: bool, detected: str, expected: str):
        self.ok = ok
        self.detected = detected
        self.expected = expected


async def validate_language(letter: str, expected_language: str) -> LanguageValidationResult:
    prompt = (
        f'Du är en språkdetektor. Svara BARA med ett JSON-objekt utan markdown.\n'
        f'Format: {{"detected": "svenska" eller "engelska", "ok": true eller false}}\n'
        f'Förväntat språk: {expected_language}\n\n'
        f'Text att analysera:\n{letter[:500]}'
    )
    raw = await llm_client.complete(prompt)
    data = _parse_json(raw)
    detected = data.get("detected", "svenska")
    return LanguageValidationResult(
        ok=bool(data.get("ok", detected == expected_language)),
        detected=detected,
        expected=expected_language,
    )


def _parse_json(text: str) -> dict:
    # strip markdown code fences if present
    text = re.sub(r"```[a-z]*\n?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # best-effort: extract first {...} block
        m = re.search(r"\{.*?\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return {}
