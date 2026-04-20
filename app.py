import asyncio

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import SearchConfig
from pipeline.init import parse_config
from pipeline.discovery.indeed import scrape_indeed
from pipeline.discovery.af_scraper import scrape_af
from pipeline.integration import build_profile
from pipeline.validators.relevance import is_relevant

app = FastAPI(title="LIA Leads Finder")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


@app.post("/search", response_class=HTMLResponse)
async def search(request: Request):
    form = await request.form()
    config = parse_config(dict(form))

    indeed_results, af_result = await asyncio.gather(
        scrape_indeed(config.tech_stack, config.city, config.all_sweden),
        scrape_af(config.tech_stack, config.city, config.all_sweden, page=config.page),
    )
    af_companies, total_af = af_result

    seen: set[str] = set()
    raw_companies = []
    for c in indeed_results + af_companies:
        key = c.name.lower().strip()
        if key not in seen:
            seen.add(key)
            raw_companies.append(c)

    profiles = [build_profile(c, config) for c in raw_companies]
    profiles = [p for p in profiles if is_relevant(p)]
    profiles.sort(key=lambda p: p.score, reverse=True)

    return templates.TemplateResponse(
        request,
        "results.html",
        {
            "profiles": profiles,
            "config": config,
            "total": total_af,
            "page": config.page,
            "page_size": 10,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
