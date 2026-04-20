from pipeline.enrichment.seniority_scorer import score_seniority

def test_lia_keyword(): assert score_seniority("LIA-plats för Python-student") == 100.0
def test_junior_keyword(): assert score_seniority("We are looking for a trainee developer") == 100.0
def test_praktikant(): assert score_seniority("Vi söker en praktikant till vårt team") == 100.0
def test_nyexaminerad(): assert score_seniority("Perfekt för nyexaminerad") == 100.0
def test_internutbildning(): assert score_seniority("Vi erbjuder internutbildning") == 100.0
def test_internship(): assert score_seniority("Looking for an internship") == 100.0

def test_intern_not_false_positive():
    assert score_seniority("internal tooling team") == 50.0
def test_senior_keyword(): assert score_seniority("Senior Python Engineer wanted") == 10.0
def test_erfaren(): assert score_seniority("Vi söker en erfaren arkitekt") == 10.0
def test_principal(): assert score_seniority("Principal Engineer role") == 10.0
def test_neutral(): assert score_seniority("Python developer at growing company") == 50.0
def test_empty(): assert score_seniority("") == 50.0

def test_junior_wins_when_both():
    assert score_seniority("junior senior developer") == 100.0
