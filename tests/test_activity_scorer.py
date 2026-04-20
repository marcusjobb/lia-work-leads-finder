from datetime import date, timedelta
from pipeline.enrichment.activity_scorer import score_activity

def test_today(): assert score_activity(date.today().isoformat()) == 100.0

def test_90_days():
    d = (date.today() - timedelta(90)).isoformat()
    assert score_activity(d) == 50.0  # 90/180 * 100 = 50

def test_180_days():
    d = (date.today() - timedelta(180)).isoformat()
    assert score_activity(d) == 0.0  # exactly 6 months = 0

def test_181_days():
    d = (date.today() - timedelta(181)).isoformat()
    assert score_activity(d) == 0.0  # older than 6 months = 0

def test_none(): assert score_activity(None) == 0.0

def test_invalid(): assert score_activity("not-a-date") == 0.0

def test_with_time_component():
    # Jobtechdev returns ISO 8601 with time
    d = date.today().isoformat() + "T09:00:00"
    assert score_activity(d) == 100.0
