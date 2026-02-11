from brisnet_parser import parse_content, parse_single_file_line
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
        _build_line({45: "Alpha", 251: "150", 1328: "100", 224: "10", 29: "10", 30: "3", 35: "10", 36: "2", 846: "95"})
    )
    r2 = parse_single_file_line(
        _build_line({45: "Beta", 251: "120", 1328: "95", 224: "20", 29: "10", 30: "1", 35: "10", 36: "1", 846: "90"})
    )
    weights = {"prime_power": 2.0, "best_speed_life": 1.0, "days_since_last": 1.0}
    rows = compute_scores([r1, r2], weights)
    assert rows[0]["horse"] == "Alpha"
    assert rows[0]["proprietary_speed_figure"] > rows[0]["bris_speed_figure"]


def test_drf_content_parses_and_uses_pace_factor():
    drf = """horse_name,track,race_date,race_number,pace_2f,pace_4f,pace_6f,late_pace,bris_speed\nFast One,SA,20250101,3,110,105,103,100,88\nLate Kick,SA,20250101,3,95,94,93,109,88\n"""
    records = parse_content(drf, source_format="drf")
    assert len(records) == 2
    assert records[0].horse_name == "Fast One"

    weights = {"recent_early_pace": 2.0, "recent_late_pace": 0.0}
    rows = compute_scores(records, weights)
    assert rows[0]["horse"] == "Fast One"


def test_proprietary_figure_tracks_bris_scale_with_zero_weights():
    horse = parse_single_file_line(_build_line({45: "Scale Check", 846: "92"}))
    rows = compute_scores([horse], weights={}, adjustment_scale=20.0)
    assert rows[0]["bris_speed_figure"] == 92.0
    assert rows[0]["proprietary_speed_figure"] == 92.0
