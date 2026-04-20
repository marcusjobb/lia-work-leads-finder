from pathlib import Path

from jinja2 import Environment, FileSystemLoader

import llm_client
from cover_letter.models import CompanyResearch, StudentProfile
from cover_letter.pipeline.postprocess import postprocess

_TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
_env = Environment(loader=FileSystemLoader(str(_TEMPLATE_DIR)), autoescape=False)


async def generate_letter(student: StudentProfile, research: CompanyResearch) -> str:
    template = _env.get_template("letter_prompt.jinja2")
    prompt = template.render(student=student, research=research)
    raw = await llm_client.complete(prompt)
    return postprocess(raw, student)
