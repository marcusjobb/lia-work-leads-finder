import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import llm_client
from cover_letter.models import CompanyResearch, StudentProfile
from cover_letter.pipeline.postprocess import postprocess

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)


def _load_example_letter() -> str | None:
    path = Path(os.getenv("EXAMPLE_LETTER_PATH", "pers-brev-example.md"))
    return path.read_text() if path.exists() else None


async def generate_letter(student: StudentProfile, research: CompanyResearch, search_mode: str = "lia") -> str:
    template = _env.get_template("letter_prompt.jinja2")
    prompt = template.render(
        student=student, research=research, example_letter=_load_example_letter(), search_mode=search_mode
    )
    raw = await llm_client.complete(prompt)
    return await postprocess(raw, student, search_mode)


async def fix_letter(
    letter: str, warnings: list[str], research: CompanyResearch, student: StudentProfile, search_mode: str = "lia"
) -> str:
    issues = "\n".join(f"- {w}" for w in warnings)
    company_ctx = research.about_text[:200] if research.about_text else ""
    values_ctx = ", ".join(research.values) if research.values else ""
    prompt = (
        f"Förbättra detta ansökningsbrev genom att åtgärda följande specifika problem:\n{issues}\n\n"
        f"Regler:\n"
        f"- Ändra BARA det som adresserar problemen ovan\n"
        f"- Behåll brevets struktur, längd och övriga formuleringar\n"
        f"- Räkna INTE fraser som klichéer om de beskriver företaget: {company_ctx}\n"
        + (f"- Företagets värderingar (ignorera dessa): {values_ctx}\n" if values_ctx else "")
        + f"\nBrev:\n{letter}"
    )
    raw = await llm_client.complete(prompt)
    return await postprocess(raw, student, search_mode)
