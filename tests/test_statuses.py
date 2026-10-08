from api.clean import clean_statuses, format_to_ics, get_station_formatted_ics

def test_clean_statuses_extracts_first_line_status():
    data = [{"id": "x", "lineStatuses": [
        {"statusSeverity": 10, "statusSeverityDescription": "Good Service"}
    ]}]
    assert clean_statuses(data) == [{
        "id": "x",
        "statusSeverity": 10,
        "statusSeverityDescription": "Good Service",
    }]

def test_clean_statuses_handles_missing_linestatuses():
    assert clean_statuses([{"id": "x"}]) == [{
        "id": "x",
        "statusSeverity": None,
        "statusSeverityDescription": None,
    }]

def test_clean_statuses_handles_empty_linestatuses():
    assert clean_statuses([{"id": "x", "lineStatuses": []}]) == [{
        "id": "x",
        "statusSeverity": None,
        "statusSeverityDescription": None,
    }]

def test_format_to_ics_skips_unknown_station(monkeypatch):
    monkeypatch.setattr("api.clean.cfg.stations", {})
    assert format_to_ics([{"id": "nope"}]) == {}

def test_format_to_ics_groups_by_ics_code(monkeypatch):
    monkeypatch.setattr("api.clean.cfg.stations", {
        "A": {"ics_code": "ICS1", "common_name": "Alpha",
              "lines": [{"id": "l1"}], "modes": ["tube"]},
    })
    out = format_to_ics([{
        "id": "A", "statusSeverity": 10,
        "statusSeverityDescription": "Good Service",
    }])
    assert out == {"ICS1": {"stations": {"A": {
        "common_name": "Alpha",
        "lines": ["l1"],
        "modes": ["tube"],
        "desc": "Good Service",
    }}}}