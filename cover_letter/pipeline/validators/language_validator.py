import re

_SWEDISH = re.compile(
    r"\b(och|att|det|är|för|med|som|på|en|ett|av|till|den|de|vi|inte|har|om)\b",
    re.IGNORECASE,
)
_ENGLISH = re.compile(
    r"\b(the|and|is|for|with|that|on|an|of|to|we|not|have|about|but|will|can)\b",
    re.IGNORECASE,
)


class LanguageValidationResult:
    def __init__(self, ok: bool, detected: str, expected: str):
        self.ok = ok
        self.detected = detected
        self.expected = expected


def validate_language(letter: str, expected_language: str) -> LanguageValidationResult:
    sv = len(_SWEDISH.findall(letter))
    en = len(_ENGLISH.findall(letter))
    detected = "svenska" if sv >= en else "engelska"
    return LanguageValidationResult(
        ok=(detected == expected_language),
        detected=detected,
        expected=expected_language,
    )
