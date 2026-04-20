from pipeline.enrichment.tech_analyzer import analyze_tech


def test_direct_match():
    score = analyze_tech(["Java", "Spring Boot"], "Senior Java Developer Spring Boot Microservices")
    assert score >= 80


def test_family_match():
    # Java student, Kotlin company — same JVM family
    score = analyze_tech(["Java"], "Kotlin backend developer, JVM experience preferred")
    assert 50 <= score < 80


def test_no_match():
    score = analyze_tech(["Java"], "Frontend React developer TypeScript")
    assert score < 30


def test_cross_family_partial():
    # Java student, C# company — different families → reduced score
    score = analyze_tech(["Java"], "Senior C# .NET developer ASP.NET")
    assert 10 <= score <= 50
