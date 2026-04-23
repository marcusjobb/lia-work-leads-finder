import re

_CLICHÉS = [
    r"\bpassionerad\b",
    r"\bdriven\b",
    r"\bexcited to\b",
    r"\bi am writing to apply\b",
    r"\bjag är en\b.{0,20}\butvecklare\b",
    r"\bseek\b.{0,20}\bopportunity\b",
    r"\bteam player\b",
    r"\boutside the box\b",
    r"\bsynergy\b",
    r"\bleverage\b",
]

_PATTERN = re.compile("|".join(_CLICHÉS), re.IGNORECASE)


class ToneValidationResult:
    def __init__(self, ok: bool, issues: list[str]):
        self.ok = ok
        self.issues = issues


def validate_tone(letter: str) -> ToneValidationResult:
    matches = _PATTERN.findall(letter)
    issues = [f'Undvik kliché: "{m}"' for m in matches]
    return ToneValidationResult(ok=len(issues) == 0, issues=issues)
