import json
import re

import llm_client
from cover_letter.models import CompanyResearch


class ToneValidationResult:
    def __init__(self, ok: bool, issues: list[str]):
        self.ok = ok
        self.issues = issues


async def validate_tone(letter: str, research: CompanyResearch | None = None) -> ToneValidationResult:
    company_context = ""
    if research:
        parts = []
        if research.about_text:
            parts.append(f"Företagsbeskrivning: {research.about_text[:300]}")
        if research.values:
            parts.append(f"Företagets värderingar: {', '.join(research.values)}")
        if parts:
            company_context = (
                "\n\nFokusera BARA på studentens egna formuleringar — inte fraser som beskriver företaget. "
                "Ignorera fraser som liknar eller parafraserar:\n" + "\n".join(parts)
            )

    prompt = (
        'Du är en HR-specialist. Identifiera följande problem i ansökningsbrevet:\n'
        '1. Klichéer/buzzwords: "passionerad", "driven", "excited to", "I am writing to apply", '
        '"lösa komplexa utmaningar", "kreativitet och innovation", "förstår helheten", '
        '"bidra till X framåt", "kommunicera lösningar till olika målgrupper"\n'
        '2. Em-streck (–) som ska ersättas med komma eller punkt\n'
        '3. Avslutning som är vag — "se fram emot att höra" utan konkret nästa steg\n'
        '4. Portfolio nämns utan att specificera vad ett projekt faktiskt visar\n'
        'Svara BARA med JSON utan markdown: {"ok": true eller false, "issues": ["issue1", ...]}\n'
        'Max 5 issues. Tom lista om inga problem.'
        f'{company_context}\n\n'
        f'Brev:\n{letter}'
    )
    raw = await llm_client.complete(prompt)
    data = _parse_json(raw)
    issues = data.get("issues", [])
    return ToneValidationResult(ok=bool(data.get("ok", len(issues) == 0)), issues=issues)


def _parse_json(text: str) -> dict:
    text = re.sub(r"```[a-z]*\n?", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*?\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
    return {}
