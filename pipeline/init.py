from models import SearchConfig


def parse_config(form_data: dict) -> SearchConfig:
    """Parse raw form POST data into SearchConfig."""
    raw_stack = form_data.get("tech_stack", "")
    tech_stack = [t.strip() for t in raw_stack.split(",") if t.strip()]

    return SearchConfig(
        city=form_data.get("city", "").strip(),
        tech_stack=tech_stack,
        all_sweden=form_data.get("all_sweden") == "on",
        program_url=form_data.get("program_url") or None,
        page=int(form_data.get("page", 1)),
    )
