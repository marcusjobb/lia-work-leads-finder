from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from models import SearchConfig
from pipeline.init import parse_config
from pipeline.discovery.indeed import scrape_indeed
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

    raw_companies = await scrape_indeed(
        config.tech_stack, config.city, config.all_sweden
    )

    profiles = [build_profile(c, config) for c in raw_companies]
    profiles = [p for p in profiles if is_relevant(p)]
    profiles.sort(key=lambda p: p.score, reverse=True)

    return templates.TemplateResponse(
        request,
        "results.html",
        {"profiles": profiles, "config": config},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
