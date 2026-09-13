import logging
import re
import llm_client
from cover_letter.models import StudentProfile
from cover_letter.pipeline.humanizer import humanize

logger = logging.getLogger(__name__)


def _strip_stray_unicode(text: str) -> str:
    """Remove non-Latin/Swedish characters that don't belong in Swedish prose."""
    return re.sub(r"[^\x00-\x7F\u00C0-\u024F\u2019\u2018\u201C\u201D\n ]", "", text)


_BANNED = [
    r"ser fram emot att (?:höra|diskutera)",
    r"bidra till \w+s? framgång",
    r"driver digital utveckling framåt",
    r"ber er återkomma om mina kunskaper",
    r"lika delar människor och innovation",
    r"komplexa tekniska problem",
    r"presentera min profil närmare",
    r"förhoppningsvis bidra till",
    r"spännande projekt",
    r"visa mitt intresse för att (?:utforska|implementera)",
]

def _flag_banned(text: str) -> list[str]:
    """Return list of banned phrases found — for logging/warnings."""
    found = []
    for pattern in _BANNED:
        if re.search(pattern, text, re.IGNORECASE):
            found.append(pattern)
    return found


async def postprocess(letter: str, student: StudentProfile, search_mode: str = "lia") -> str:
    portfolio = student.portfolio_url or "inga"
    prompt = (
        f'Städa detta ansökningsbrev:\n'
        f'- Ta bort telefonnummer och e-postadresser\n'
        f'- Ta bort URLs UTOM: {portfolio}\n'
        f'- Ta bort tomma rader i slutet\n'
        f'- Ändra INGET annat — returnera bara den städade texten, ingen kommentar\n\n'
        f'Brev:\n{letter}'
    )
    cleaned = await llm_client.complete(prompt)
    cleaned = _strip_stray_unicode(cleaned.rstrip())
    result = await humanize(cleaned, search_mode)
    banned = _flag_banned(result)
    if banned:
        logger.warning("Banned phrases still in letter after humanize: %s", banned)
    return result
