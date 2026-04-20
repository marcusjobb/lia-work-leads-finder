import logging
import re
import httpx
from bs4 import BeautifulSoup
from models import ContactInfo

logger = logging.getLogger(__name__)

CONTACT_PATHS = ["/kontakt", "/contact", "/kontakta", "/about/contact"]
CAREERS_PATHS = ["/karriar", "/karriär", "/career", "/careers", "/jobs", "/lediga-tjanster"]


async def find_contact(website: str | None) -> tuple[ContactInfo, float]:
    """Scrape company website for contact info. Returns (ContactInfo, score 0–100)."""
    if not website:
        return ContactInfo(), 0.0
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            response = await client.get(website)
            response.raise_for_status()
            html = response.text
    except Exception as exc:
        logger.warning("ContactFinder failed for %s: %s", website, exc)
        return ContactInfo(), 0.0

    soup = BeautifulSoup(html, "html.parser")

    for tag in soup.find_all("a", href=re.compile(r"^mailto:", re.I)):
        email = re.sub(r"^mailto:", "", tag["href"], flags=re.I).strip().split("?")[0]
        if email:
            return ContactInfo(email=email), 100.0

    contact_url = next(
        (tag["href"] for tag in soup.find_all("a", href=True)
         if any(p in tag["href"].lower() for p in CONTACT_PATHS)),
        None,
    )
    careers_page = next(
        (tag["href"] for tag in soup.find_all("a", href=True)
         if any(p in tag["href"].lower() for p in CAREERS_PATHS)),
        None,
    )
    if contact_url or careers_page:
        return ContactInfo(contact_url=contact_url, careers_page=careers_page), 60.0

    return ContactInfo(), 0.0
