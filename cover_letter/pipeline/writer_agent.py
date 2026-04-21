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


async def generate_letter(student: StudentProfile, research: CompanyResearch) -> str:
    template = _env.get_template("letter_prompt.jinja2")
    prompt = template.render(student=student, research=research, example_letter=_load_example_letter())
    raw = await llm_client.complete(prompt)
    return postprocess(raw, student)
