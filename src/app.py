import asyncio
import json
import logging
import logging.config
from pathlib import Path
from urllib.parse import unquote

import yaml
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from cover_letter.models import CompanyResearch, StudentProfile
from cover_letter.pipeline.research_agent import research_company
from cover_letter.pipeline.validators.language_validator import validate_language
from cover_letter.pipeline.validators.tone_validator import validate_tone
from cover_letter.pipeline.writer_agent import fix_letter, generate_letter
from export.docx_exporter import export_letter
from export.xlsx_exporter import export_leads
from models import CompanyRaw, LeadProfile, SearchConfig
from pipeline.init import parse_config
from pipeline.discovery.indeed import scrape_indeed
from pipeline.discovery.af_scraper import scrape_af, PAGE_SIZE
from pipeline.discovery.company_scraper import scrape_companies
from pipeline.integration import build_profile_async, build_profile_fast
from pipeline.enrichment.program_scraper import scrape_program, extract_keywords_from_pdf
from pipeline.enrichment.geocoder import geocode
from pipeline.validators.relevance import is_relevant
from pipeline.validators.completeness import is_complete
from pipeline.validators.contact import is_reachable

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s — %(message)s",
)

_ROOT = Path(__file__).parent.parent

app = FastAPI(title="LIA Leads Finder")
app.mount("/static", StaticFiles(directory=str(_ROOT / "static")), name="static")
templates = Jinja2Templates(directory=str(_ROOT / "templates"))

_CACHE_DIR = _ROOT / "cache"
_RESULTS_CACHE = _CACHE_DIR / "last_results.json"
_LETTERS_CACHE = _CACHE_DIR / "letters"
_TOP_N = 30  # full enrichment (stability API + contact) for top N candidates only


def _save_profiles(profiles: list[LeadProfile]) -> None:
    _CACHE_DIR.mkdir(exist_ok=True)
    _RESULTS_CACHE.write_text(
        json.dumps([p.model_dump() for p in profiles], ensure_ascii=False, indent=2)
    )


def _load_profiles() -> list[LeadProfile]:
    if not _RESULTS_CACHE.exists():
        return []
    data = json.loads(_RESULTS_CACHE.read_text())
    return [LeadProfile(**d) for d in data]


def _find_profile(company_name: str) -> LeadProfile | None:
    for p in _load_profiles():
        if p.company_name == company_name:
            return p
    return None


def _load_student() -> StudentProfile:
    path = Path("student_profile.yaml")
    if not path.exists():
        return StudentProfile(
            name="Student",
            education="YH-utbildning",
            tech_stack=[],
            experience="",
            languages=["svenska"],
            bio="",
        )
    data = yaml.safe_load(path.read_text())
    return StudentProfile(**data)


def _save_letter(company_name: str, letter: str) -> None:
    _LETTERS_CACHE.mkdir(parents=True, exist_ok=True)
    safe = company_name.replace("/", "_").replace(" ", "_")
    (_LETTERS_CACHE / f"{safe}.txt").write_text(letter)


def _load_letter(company_name: str) -> str | None:
    safe = company_name.replace("/", "_").replace(" ", "_")
    path = _LETTERS_CACHE / f"{safe}.txt"
    return path.read_text() if path.exists() else None


def _save_research(company_name: str, research: CompanyResearch) -> None:
    _LETTERS_CACHE.mkdir(parents=True, exist_ok=True)
    safe = company_name.replace("/", "_").replace(" ", "_")
    (_LETTERS_CACHE / f"{safe}_research.json").write_text(research.model_dump_json())


def _load_research(company_name: str) -> CompanyResearch | None:
    safe = company_name.replace("/", "_").replace(" ", "_")
    path = _LETTERS_CACHE / f"{safe}_research.json"
    return CompanyResearch.model_validate_json(path.read_text()) if path.exists() else None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    student = _load_student()
    return templates.TemplateResponse(request, "index.html", {"student": student})


@app.get("/profile", response_class=HTMLResponse)
async def profile_form(request: Request, saved: bool = False, keywords: str = ""):
    student = _load_student()
    analyzed = [k.strip() for k in keywords.split(",") if k.strip()]
    return templates.TemplateResponse(request, "profile.html", {
        "student": student,
        "saved": saved,
        "analyzed_keywords": analyzed,
    })


@app.post("/profile/analyze-url")
async def analyze_program_url(request: Request):
    form = await request.form()
    url = form.get("program_url", "").strip()
    if not url:
        return RedirectResponse("/profile", status_code=303)
    scraped = await scrape_program(url)
    student = _load_student()
    # Merge: scraped first (new findings), then existing tech_stack — deduped, order preserved
    merged = list(dict.fromkeys(scraped + student.tech_stack))
    return RedirectResponse(f"/profile?keywords={','.join(merged)}", status_code=303)


@app.post("/profile/analyze-pdf")
async def analyze_pdf_upload(request: Request, pdf: UploadFile = File(...)):
    data = await pdf.read()
    scraped = await extract_keywords_from_pdf(data)
    student = _load_student()
    merged = list(dict.fromkeys(scraped + student.tech_stack))
    return RedirectResponse(f"/profile?keywords={','.join(merged)}", status_code=303)


@app.post("/profile", response_class=HTMLResponse)
async def profile_save(request: Request):
    form = await request.form()

    checked = list(form.getlist("checked_keywords"))
    custom = [t.strip() for t in form.get("custom_buzzwords", "").split(",") if t.strip()]
    text_input = [t.strip() for t in form.get("tech_stack", "").split(",") if t.strip()]
    tech_stack = list(dict.fromkeys(checked + custom)) or text_input

    languages = [l.strip() for l in form.get("languages", "").split(",") if l.strip()]
    portfolio_url = form.get("portfolio_url", "").strip() or None
    program_url = form.get("program_url", "").strip() or None
    lia_period = form.get("lia_period", "").strip() or None

    data = {
        "name": form.get("name", "").strip(),
        "education": form.get("education", "").strip(),
        "tech_stack": tech_stack,
        "experience": form.get("experience", "").strip(),
        "languages": languages or ["svenska"],
        "portfolio_url": portfolio_url,
        "program_url": program_url,
        "bio": form.get("bio", "").strip(),
        "lia_period": lia_period,
    }
    Path("student_profile.yaml").write_text(yaml.dump(data, allow_unicode=True, sort_keys=False))

    student = StudentProfile(**data)
    return templates.TemplateResponse(request, "profile.html", {"student": student, "saved": True, "analyzed_keywords": []})


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request):
    form = await request.form()
    config = parse_config(dict(form))

    if config.program_url and not config.tech_stack:
        config = config.model_copy(update={"tech_stack": await scrape_program(config.program_url)})

    indeed_results, af_result, allabolag_results = await asyncio.gather(
        scrape_indeed(config.tech_stack, config.city, config.all_sweden),
        scrape_af(config.tech_stack, config.city, config.all_sweden, radius_km=config.radius_km),
        scrape_companies(config.tech_stack, config.city),
    )
    af_companies, total_af = af_result

    raw_companies = indeed_results + af_companies + allabolag_results

    center_coords = await geocode(config.city) if config.radius_km > 0 else None

    # Pass 1 — fast scoring without API calls, used to rank all candidates
    fast_profiles = list(await asyncio.gather(*[build_profile_fast(c, config, center_coords) for c in raw_companies]))
    fast_profiles = [p for p in fast_profiles if is_relevant(p) and is_complete(p) and is_reachable(p)]
    fast_profiles.sort(key=lambda p: p.score, reverse=True)

    # Pass 2 — full enrichment (stability API + contact) for top N only
    name_to_raw = {c.name: c for c in raw_companies}
    top_raw = [name_to_raw[p.company_name] for p in fast_profiles[:_TOP_N] if p.company_name in name_to_raw]
    enriched = list(await asyncio.gather(*[build_profile_async(c, config, center_coords) for c in top_raw]))

    enriched_names = {p.company_name for p in enriched}
    rest = [p for p in fast_profiles[_TOP_N:] if p.company_name not in enriched_names]
    all_profiles = sorted(enriched + rest, key=lambda p: p.score, reverse=True)

    seen: set[str] = set()
    all_profiles = [p for p in all_profiles if not (p.company_name in seen or seen.add(p.company_name))]  # type: ignore[func-returns-value]

    _save_profiles(all_profiles)

    page = config.page
    page_size = config.page_size
    start = (page - 1) * page_size
    profiles_page = all_profiles[start : start + page_size]
    total_scored = len(all_profiles)

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "profiles": profiles_page,
            "config": config,
            "total": total_scored,
            "page": page,
            "page_size": page_size,
        },
    )


@app.get("/lead", response_class=HTMLResponse)
async def lead_detail(request: Request, name: str = "", enriched: bool = False):
    profile = _find_profile(name)
    if not profile:
        return HTMLResponse("<p>Lead hittades inte. <a href='/'>Ny sökning</a></p>", status_code=404)
    return templates.TemplateResponse(request, "lead_detail.html", {"profile": profile, "enriched": enriched})


@app.post("/enrich")
async def enrich_lead(request: Request):
    form = await request.form()
    company_name = form.get("company_name", "")
    profile = _find_profile(company_name)
    if not profile:
        return HTMLResponse("<p>Lead hittades inte.</p>", status_code=404)

    raw = CompanyRaw(
        name=profile.company_name,
        city=profile.city,
        website=profile.website,
        source=profile.source,
        job_title=profile.job_title,
        job_url=profile.job_url,
    )
    config = SearchConfig(city=profile.city, tech_stack=profile.tech_tags or [""], search_mode=profile.search_mode)
    enriched_profile = await build_profile_async(raw, config)

    profiles = _load_profiles()
    profiles = [enriched_profile if p.company_name == company_name else p for p in profiles]
    _save_profiles(profiles)

    return RedirectResponse(f"/lead?name={company_name}&enriched=1", status_code=303)


@app.get("/export-leads")
async def export_leads_route():
    profiles = _load_profiles()
    if not profiles:
        return HTMLResponse("<p>Ingen sökning gjord än.</p>", status_code=404)
    out = _CACHE_DIR / "leads_export.xlsx"
    export_leads(profiles, out)
    return FileResponse(
        out,
        filename="lia-leads.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@app.get("/cover-letter", response_class=HTMLResponse)
async def cover_letter_form(request: Request, company: str = ""):
    company = unquote(company)
    lead = _find_profile(company)
    student = _load_student()
    return templates.TemplateResponse(
        request,
        "cover_letter.html",
        {"lead": lead, "student": student, "letter": None, "error": None},
    )


@app.post("/generate-letter", response_class=HTMLResponse)
async def generate_letter_route(request: Request):
    form = await request.form()
    company_name = form.get("company_name", "")
    lead = _find_profile(company_name)
    student = _load_student()

    if not lead:
        return templates.TemplateResponse(
            request,
            "cover_letter.html",
            {"lead": None, "student": student, "letter": None, "error": "Företaget hittades inte i cache. Gör en ny sökning."},
        )

    try:
        research = await research_company(lead)
        letter = await generate_letter(student, research)
        _save_letter(company_name, letter)
        _save_research(company_name, research)

        tone = await validate_tone(letter, research)
        lang = await validate_language(letter, research.detected_language)
        warnings = tone.issues + ([] if lang.ok else [f"Språk: förväntat {lang.expected}, fick {lang.detected}"])
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "cover_letter.html",
            {"lead": lead, "student": student, "letter": None, "error": str(e)},
        )

    return templates.TemplateResponse(
        request,
        "cover_letter.html",
        {"lead": lead, "student": student, "letter": letter, "warnings": warnings, "error": None},
    )


@app.post("/fix-letter", response_class=HTMLResponse)
async def fix_letter_route(request: Request):
    form = await request.form()
    company_name = form.get("company_name", "")
    current_letter = form.get("current_letter", "")
    lead = _find_profile(company_name)
    student = _load_student()
    research = _load_research(company_name)

    if not lead or not research:
        return RedirectResponse("/generate-letter", status_code=303)

    try:
        tone_before = await validate_tone(current_letter, research)
        lang_before = await validate_language(current_letter, research.detected_language)
        warnings_before = tone_before.issues + ([] if lang_before.ok else [f"Språk: förväntat {lang_before.expected}, fick {lang_before.detected}"])

        letter = await fix_letter(current_letter, warnings_before, research, student)
        _save_letter(company_name, letter)

        tone = await validate_tone(letter, research)
        lang = await validate_language(letter, research.detected_language)
        warnings = tone.issues + ([] if lang.ok else [f"Språk: förväntat {lang.expected}, fick {lang.detected}"])
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "cover_letter.html",
            {"lead": lead, "student": student, "letter": current_letter, "error": str(e)},
        )

    return templates.TemplateResponse(
        request,
        "cover_letter.html",
        {"lead": lead, "student": student, "letter": letter, "warnings": warnings, "error": None},
    )


@app.get("/download-letter")
async def download_letter(company: str = ""):
    company = unquote(company)
    letter = _load_letter(company)
    lead = _find_profile(company)
    student = _load_student()

    if not letter or not lead:
        return HTMLResponse("<p>Inget brev genererat. Gå tillbaka och generera ett brev först.</p>", status_code=404)

    out = _CACHE_DIR / "brev.docx"
    export_letter(letter, student, lead.company_name, out)
    return FileResponse(
        out,
        filename=f"ansokningsbrev-{lead.company_name.replace(' ', '-')}.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
