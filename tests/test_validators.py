from models import ContactInfo, LeadProfile, ScoreBreakdown
from pipeline.validators.completeness import is_complete
from pipeline.validators.contact import is_reachable
from cover_letter.pipeline.validators.language_validator import validate_language
from cover_letter.pipeline.validators.tone_validator import validate_tone


def _profile(**kwargs) -> LeadProfile:
    defaults = dict(
        company_name="Test AB", city="Göteborg", source="af",
        tech_tags=[], contact=ContactInfo(),
        score=50.0,
        score_breakdown=ScoreBreakdown(
            tech_match=50, geo=50, contact=0, activity=50, stability=50, seniority=50
        ),
        match_reason="test", tier="GOOD",
    )
    defaults.update(kwargs)
    return LeadProfile(**defaults)


# --- Phase 1: completeness + contact validators ---

def test_complete_with_name_and_city():
    assert is_complete(_profile()) is True


def test_incomplete_missing_city():
    p = _profile()
    p.city = ""
    assert is_complete(p) is False


def test_reachable_via_email():
    assert is_reachable(_profile(contact=ContactInfo(email="hr@test.se"))) is True


def test_reachable_via_contact_url():
    assert is_reachable(_profile(contact=ContactInfo(contact_url="https://test.se/kontakt"))) is True


def test_reachable_via_website():
    assert is_reachable(_profile(website="https://test.se")) is True


def test_reachable_via_job_url():
    assert is_reachable(_profile(job_url="https://af.se/job/1")) is True


def test_not_reachable_no_contact():
    assert is_reachable(_profile()) is False


# --- Phase 2: tone + language validators ---

def test_tone_clean_letter():
    letter = "Jag söker LIA-plats hos er eftersom ert arbete med molntjänster är intressant."
    assert validate_tone(letter).ok


def test_tone_detects_cliché_passionerad():
    result = validate_tone("Jag är passionerad av Java och vill gärna jobba hos er.")
    assert not result.ok
    assert any("passionerad" in issue for issue in result.issues)


def test_tone_detects_excited_to():
    assert not validate_tone("I am excited to apply for this position.").ok


def test_language_swedish_matches():
    result = validate_language("Jag vill söka praktikplats hos er och bidra med mitt kunnande inom Java.", "svenska")
    assert result.ok and result.detected == "svenska"


def test_language_english_matches():
    result = validate_language("I would like to apply for an internship and contribute with my knowledge of Java.", "engelska")
    assert result.ok and result.detected == "engelska"


def test_language_mismatch():
    result = validate_language("Jag vill söka praktikplats hos er och bidra med mitt kunnande.", "engelska")
    assert not result.ok
