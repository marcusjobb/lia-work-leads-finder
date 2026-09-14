from models import SearchConfig


def parse_config(form_data: dict) -> SearchConfig:
    """Parse raw form POST data into SearchConfig."""
    raw_stack = form_data.get("tech_stack", "")
    tech_stack = [t.strip() for t in raw_stack.split(",") if t.strip()]

    search_mode = form_data.get("search_mode", "lia")
    if search_mode not in ("lia", "junior", "senior", "any"):
        search_mode = "lia"

    return SearchConfig(
        city=form_data.get("city", "").strip(),
        tech_stack=tech_stack,
        all_sweden=form_data.get("all_sweden") == "on",
        program_url=form_data.get("program_url") or None,
        radius_km=int(form_data.get("radius_km", 0)),
        page=int(form_data.get("page", 1)),
        page_size=int(form_data.get("page_size", 10)),
        search_mode=search_mode,
    )
