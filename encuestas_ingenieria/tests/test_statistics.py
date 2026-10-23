from services.estadisticas_service import _distribution

def test_distribution_calculates_frequency_and_percentages():
    rows = _distribution(["Facebook", "Facebook", "TikTok"], ["Facebook", "TikTok", "Instagram"])
    assert rows[0]["count"] == 2
    assert rows[0]["relative_frequency"] == 0.6667
    assert rows[0]["percentage"] == 66.67
    assert rows[2]["count"] == 0
    assert rows[1]["percentage"] == 33.33

def test_empty_distribution_does_not_divide_by_zero():
    rows = _distribution([], ["Facebook"])
    assert rows == [{"label": "Facebook", "count": 0, "relative_frequency": 0, "percentage": 0}]
