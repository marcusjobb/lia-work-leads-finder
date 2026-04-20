import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import SearchConfig
from pipeline.init import parse_config
from pipeline.discovery.indeed import scrape_indeed
from pipeline.discovery.af_scraper import scrape_af, PAGE_SIZE
from pipeline.integration import build_profile_async
from pipeline.validators.relevance import is_relevant

app = FastAPI(title="LIA Leads Finder")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

_results_cache: dict[str, object] = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request):
    form = await request.form()
    config = parse_config(dict(form))

    indeed_results, af_result = await asyncio.gather(
        scrape_indeed(config.tech_stack, config.city, config.all_sweden),
        scrape_af(config.tech_stack, config.city, config.all_sweden, page=config.page, page_size=config.page_size),
    )
    af_companies, total_af = af_result

    raw_companies = indeed_results + af_companies

    profiles = list(await asyncio.gather(*[build_profile_async(c, config) for c in raw_companies]))
    profiles = [p for p in profiles if is_relevant(p)]
    profiles.sort(key=lambda p: p.score, reverse=True)

    _results_cache.clear()
    for p in profiles:
        _results_cache[p.company_name] = p

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "profiles": profiles,
            "config": config,
            "total": total_af,
            "page": config.page,
            "page_size": config.page_size,
        },
    )


@app.get("/lead", response_class=HTMLResponse)
async def lead_detail(request: Request, name: str = ""):
    profile = _results_cache.get(name)
    if not profile:
        return HTMLResponse("<p>Lead hittades inte. <a href='/'>Ny sökning</a></p>", status_code=404)
    return templates.TemplateResponse(request, "lead_detail.html", {"profile": profile})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
