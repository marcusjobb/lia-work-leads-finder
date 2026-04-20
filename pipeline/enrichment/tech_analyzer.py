"""Tech stack analyzer — matches student skills against company job descriptions."""

STACK_FAMILIES: dict[str, list[str]] = {
    "java": ["java", "kotlin", "spring", "maven", "gradle", "jvm"],
    "csharp": ["c#", "csharp", ".net", "dotnet", "asp.net", "asp", "blazor", "azure"],
    "python": ["python", "django", "fastapi", "flask", "pandas"],
    "javascript": ["javascript", "typescript", "node.js", "node", "react", "vue", "angular"],
    "devops": ["docker", "kubernetes", "terraform", "ci/cd", "github actions"],
}


def _families_for(terms: list[str]) -> set[str]:
    """Return all stack families matching any of the given terms."""
    result = set()
    for term in terms:
        t = term.lower().strip()
        for family, keywords in STACK_FAMILIES.items():
            # Match: keyword is in term (as substring) OR term is exact keyword
            if any(kw in t for kw in keywords):
                result.add(family)
                break  # Each term matches only one family (first match wins)
    return result


def analyze_tech(tech_stack: list[str], text: str) -> float:
    """
    Return 0–100 tech match score.

    Strategy:
    1. Direct keyword hits: each tech in tech_stack found in text → high score
    2. Family match: student and company use same stack family (e.g. JVM) → medium score
    3. Cross-family: different families → low score
    4. No match: no recognizable tech → baseline 10
    """
    text_lower = text.lower()

    # Direct keyword hits
    hits = sum(1 for t in tech_stack if t.lower() in text_lower)
    if hits > 0:
        return min(100.0, (hits / len(tech_stack)) * 100)

    student_families = _families_for(tech_stack)
    text_terms = text_lower.split()
    company_families = _families_for(text_terms)

    if not company_families:
        return 10.0

    if student_families & company_families:
        return 60.0  # same family, no direct keyword hit

    return 25.0  # cross-family (adjacent tech)
