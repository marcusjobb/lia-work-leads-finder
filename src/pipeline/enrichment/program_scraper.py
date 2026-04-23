import io
import ipaddress
import json
import re
from urllib.parse import urlparse

import httpx
import pdfplumber
from bs4 import BeautifulSoup
from llm_client import complete


def _is_safe_url(url: str) -> bool:
    """Reject private IPs, loopback, and non-http(s) schemes to prevent SSRF."""
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.hostname or ""
        if not host:
            return False
        try:
            addr = ipaddress.ip_address(host)
            return not (addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved)
        except ValueError:
            return host.lower() not in ("localhost", "0.0.0.0")
    except Exception:
        return False

KNOWN_TECH = [
    # Languages
    "Python", "Java", "JavaScript", "TypeScript", "C#", "C++",
    "Kotlin", "Swift", "Go", "Rust", "PHP", "Ruby",
    # Frontend
    "React", "Vue", "Angular", "Node.js", "HTML", "CSS",
    # Backend frameworks
    "Spring Boot", "Spring", "Django", "FastAPI", "Flask", ".NET",
    # Data & databases
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Databaser",
    "JPA", "Hibernate",
    # DevOps & cloud
    "Docker", "Kubernetes", "Terraform", "DevOps", "CI/CD",
    "AWS", "Azure", "GCP", "Linux", "Git",
    # Java ecosystem
    "Maven", "Gradle", "JUnit", "REST", "Microservices",
    # Agile & process
    "Scrum", "Agile",
]

def _build_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term)
    return re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)

_PATTERNS: list[tuple[str, re.Pattern]] = [
    (term, _build_pattern(term)) for term in KNOWN_TECH
]


def _match_keywords(text: str) -> list[str]:
    matched: list[str] = []
    seen: set[str] = set()
    for canonical, pattern in _PATTERNS:
        if canonical not in seen and pattern.search(text):
            matched.append(canonical)
            seen.add(canonical)
    return matched


async def _extract_with_ai(text: str) -> list[str]:
    """Send program text to LLM, return list of tech keywords. Empty list on failure."""
    if not text.strip():
        return []
    prompt = (
        "Extract technology keywords relevant to a software developer's CV from this educational program description. "
        "Include: programming languages, frameworks, libraries, databases, cloud platforms, DevOps tools, "
        "version control, methodologies (Agile/Scrum/Kanban), and tech-specific course names. "
        "Exclude: hardware specs (CPU, RAM, SSD, GPU), operating system versions (Windows 11, macOS), "
        "general terms (Internet, IT), and non-tech administrative terms. "
        "Return ONLY a JSON array of strings, no explanation. "
        'Example: ["Java", "Spring Boot", "SQL", "Docker", "Git", "Scrum", "REST"]\n\n'
        f"Text:\n{text[:8000]}"
    )
    try:
        response = await complete(prompt)
        match = re.search(r"\[.*?\]", response, re.DOTALL)
        if match:
            items = json.loads(match.group())
            return [str(i).strip() for i in items if str(i).strip()]
    except Exception:
        pass
    return []


async def _extract_from_pdf_bytes(data: bytes) -> list[str]:
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        text = " ".join(page.extract_text() or "" for page in pdf.pages)
    ai = await _extract_with_ai(text)
    return ai or _match_keywords(text)


async def scrape_program(url: str) -> list[str]:
    """Fetch a program page (HTML or PDF URL) and extract tech stack keywords.
    For HTML pages, also fetches any linked PDFs to get full course details."""
    if not _is_safe_url(url):
        return []
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=False) as client:
            response = await client.get(url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "pdf" in content_type or url.lower().endswith(".pdf"):
                return await _extract_from_pdf_bytes(response.content)

            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator=" ")

            # Also fetch linked PDFs on the page (course plans, curricula)
            base = url.rsplit("/", 1)[0]
            pdf_links = [
                tag["href"] if tag["href"].startswith("http") else base + "/" + tag["href"].lstrip("/")
                for tag in soup.find_all("a", href=True)
                if tag["href"].lower().endswith(".pdf")
            ]
            pdf_text = ""
            for pdf_url in pdf_links[:2]:  # max 2 PDFs to keep it fast
                if not _is_safe_url(pdf_url):
                    continue
                try:
                    pdf_resp = await client.get(pdf_url)
                    pdf_resp.raise_for_status()
                    with pdfplumber.open(io.BytesIO(pdf_resp.content)) as pdf:
                        pdf_text += " " + " ".join(page.extract_text() or "" for page in pdf.pages)
                except Exception:
                    pass
            # PDF first — it has the course list; HTML page is appended for context
            if pdf_text:
                text = pdf_text + " " + text

        ai = await _extract_with_ai(text)
        return ai or _match_keywords(text)
    except Exception:
        return []





async def extract_keywords_from_pdf(data: bytes) -> list[str]:
    """Extract keywords from raw PDF bytes (for file upload)."""
    try:
        return await _extract_from_pdf_bytes(data)
    except Exception:
        return []
