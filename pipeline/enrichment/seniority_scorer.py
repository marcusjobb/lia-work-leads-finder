JUNIOR_SIGNALS = {
    "junior", "trainee", "praktikant", "lärling", "nybörjare",
    "nyexaminerad", "nyutexaminerad", "entry level", "lia", "praktik",
    "internship", "intern", "internutbildning",
}
SENIOR_SIGNALS = {
    "senior", "lead", "principal", "architect", "arkitekt",
    "erfaren", "expert", "staff",
}


def score_seniority(text: str) -> float:
    """Return 0–100. 100=junior/LIA role, 10=senior role, 50=neutral. Junior wins on tie."""
    text_lower = text.lower()
    if any(s in text_lower for s in JUNIOR_SIGNALS):
        return 100.0
    if any(s in text_lower for s in SENIOR_SIGNALS):
        return 10.0
    return 50.0
