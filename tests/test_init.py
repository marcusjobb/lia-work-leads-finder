from pipeline.init import parse_config


def test_basic_parse():
    config = parse_config({"city": "Göteborg", "tech_stack": "Java, Spring Boot"})
    assert config.city == "Göteborg"
    assert config.tech_stack == ["Java", "Spring Boot"]
    assert config.all_sweden is False


def test_all_sweden_checkbox():
    config = parse_config({"city": "Stockholm", "tech_stack": "Python", "all_sweden": "on"})
    assert config.all_sweden is True


def test_all_sweden_absent():
    config = parse_config({"city": "Malmö", "tech_stack": "React"})
    assert config.all_sweden is False


def test_empty_program_url():
    config = parse_config({"city": "Uppsala", "tech_stack": "Java", "program_url": ""})
    assert config.program_url is None


def test_search_mode_defaults_to_lia():
    config = parse_config({"city": "Göteborg", "tech_stack": "Java"})
    assert config.search_mode == "lia"


def test_search_mode_senior():
    config = parse_config({"city": "Göteborg", "tech_stack": "Java", "search_mode": "senior"})
    assert config.search_mode == "senior"


def test_search_mode_junior():
    config = parse_config({"city": "Göteborg", "tech_stack": "Java", "search_mode": "junior"})
    assert config.search_mode == "junior"


def test_search_mode_invalid_falls_back_to_lia():
    config = parse_config({"city": "Göteborg", "tech_stack": "Java", "search_mode": "bogus"})
    assert config.search_mode == "lia"
