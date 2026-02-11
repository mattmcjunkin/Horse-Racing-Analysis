from brisnet_parser import parse_single_file_line
from scoring import compute_scores


def _build_line(overrides: dict[int, str]) -> str:
    fields = [""] * 1435
    for idx, val in overrides.items():
        fields[idx - 1] = val
    return ",".join(fields)


def test_parse_line_and_accessors():
    line = _build_line({1: "GP", 2: "20250101", 3: "5", 45: "Speedy"})
    record = parse_single_file_line(line)
    assert record.track == "GP"
    assert record.race_number == 5
    assert record.horse_name == "Speedy"


def test_compute_scores_orders_highest_weighted_horse_first():
    r1 = parse_single_file_line(
        _build_line({45: "Alpha", 251: "150", 1328: "100", 224: "10", 29: "10", 30: "3", 35: "10", 36: "2"})
    )
    r2 = parse_single_file_line(
        _build_line({45: "Beta", 251: "120", 1328: "95", 224: "20", 29: "10", 30: "1", 35: "10", 36: "1"})
    )
    weights = {"prime_power": 3.0, "best_speed_life": 1.0, "days_since_last": 1.0}
    rows = compute_scores([r1, r2], weights)
    assert rows[0]["horse"] == "Alpha"
