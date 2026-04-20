from cover_letter.models import StudentProfile
from cover_letter.pipeline.postprocess import postprocess

STUDENT = StudentProfile(
    name="Nisse Nilsson",
    education="YH Java-utvecklare",
    tech_stack=["Java"],
    experience="2 år support",
    languages=["svenska"],
    portfolio_url="https://github.com/nissenilsson",
    bio="Lösningsorienterad",
)


def test_removes_phone_number():
    letter = "Bra brev.\n\nNisse Nilsson\n073–456 78 90"
    result = postprocess(letter, STUDENT)
    assert "073" not in result
    assert "456 78 90" not in result


def test_removes_placeholder_email():
    letter = "Bra brev.\n\nNisse Nilsson\nnisse@email.se"
    result = postprocess(letter, STUDENT)
    assert "@" not in result


def test_keeps_portfolio_url():
    letter = "Se min portfolio: https://github.com/nissenilsson"
    result = postprocess(letter, STUDENT)
    assert "github.com/nissenilsson" in result


def test_removes_unrelated_url():
    letter = "Besök https://randomsite.com för mer info."
    result = postprocess(letter, STUDENT)
    assert "randomsite.com" not in result


def test_preserves_letter_body():
    letter = "Hej,\n\nJag söker LIA hos er.\n\nMed vänliga hälsningar,\nNisse Nilsson"
    result = postprocess(letter, STUDENT)
    assert "Jag söker LIA hos er." in result
    assert "Nisse Nilsson" in result


def test_strips_trailing_blank_lines():
    letter = "Bra brev.\n073–123 45 67\n\n\n"
    result = postprocess(letter, STUDENT)
    assert not result.endswith("\n")


def test_no_double_spaces_after_removal():
    letter = "Kontakt: 073–123 45 67 och nisse@email.se tack."
    result = postprocess(letter, STUDENT)
    assert "  " not in result
