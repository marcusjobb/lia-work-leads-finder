import re
import httpx
from bs4 import BeautifulSoup

KNOWN_TECH = [
    "Python", "Java", "JavaScript", "TypeScript", "C#", "C++",
    "Kotlin", "Swift", "Go", "Rust", "PHP", "Ruby",
    "React", "Vue", "Angular", "Node.js",
    "Spring", "Django", "FastAPI", "Flask", ".NET",
    "Docker", "Kubernetes", "Terraform",
    "PostgreSQL", "MySQL", "MongoDB", "Redis",
    "AWS", "Azure", "GCP",
    "Linux", "Git",
]

# Pre-compile patterns. Use word boundaries, but handle special chars in names.
# For "C#", "C++", ".NET", "Node.js" — use lookahead/lookbehind for non-alnum context.
def _build_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term)
    # Word boundary \b works on \w chars. For terms ending/starting with special chars,
    # use negative lookahead/lookbehind for word characters.
    return re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)

_PATTERNS: list[tuple[str, re.Pattern]] = [
    (term, _build_pattern(term)) for term in KNOWN_TECH
]


async def scrape_program(url: str) -> list[str]:
    """Fetch a program page URL and extract tech stack keywords. Returns list of tech terms."""
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            html = response.text

        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text(separator=" ")

        matched: list[str] = []
        seen: set[str] = set()
        for canonical, pattern in _PATTERNS:
            if canonical not in seen and pattern.search(text):
                matched.append(canonical)
                seen.add(canonical)

        return matched
    except Exception:
        return []
