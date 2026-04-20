from pipeline.enrichment.geo_scorer import score_geo


def test_exact_city_match():
    assert score_geo("Göteborg", "Göteborg", all_sweden=False) == 100.0


def test_partial_city_match():
    # "Göteborg" is in "Göteborg, Sverige"
    assert score_geo("Göteborg, Sverige", "Göteborg", all_sweden=False) == 100.0


def test_different_city():
    score = score_geo("Stockholm", "Göteborg", all_sweden=False)
    assert score == 30.0


def test_all_sweden():
    score = score_geo("Kiruna", "Göteborg", all_sweden=True)
    assert score == 60.0
