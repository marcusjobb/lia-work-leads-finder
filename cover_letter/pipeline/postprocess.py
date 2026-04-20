import re

from cover_letter.models import StudentProfile

_PHONE = re.compile(r"\b(?:\+46|0)\d[\d\s\-–]{6,}\d\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.\w{2,}\b")
_URL = re.compile(r"https?://\S+|www\.\S+")


def postprocess(letter: str, student: StudentProfile) -> str:
    lines = letter.splitlines()
    cleaned = [_clean_line(line, student) for line in lines]
    # strip trailing blank lines introduced by removals
    while cleaned and not cleaned[-1].strip():
        cleaned.pop()
    return "\n".join(cleaned)


def _clean_line(line: str, student: StudentProfile) -> str:
    # remove phone numbers unconditionally (not in StudentProfile)
    line = _PHONE.sub("", line)

    # remove emails unconditionally (not in StudentProfile)
    line = _EMAIL.sub("", line)

    # remove URLs unless they match the student's portfolio
    def _keep_url(m: re.Match) -> str:
        url = m.group()
        if student.portfolio_url and student.portfolio_url.rstrip("/") in url.rstrip("/"):
            return url
        return ""

    line = _URL.sub(_keep_url, line)

    # collapse multiple spaces and strip trailing whitespace
    line = re.sub(r"  +", " ", line).rstrip()
    return line
