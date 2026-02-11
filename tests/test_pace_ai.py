from pace_ai import build_pace_map, classify_race_pace


def test_classify_fast_pace():
    rows = [
        {"horse": "A", "recent_early_pace": 108, "run_style": "E"},
        {"horse": "B", "recent_early_pace": 106, "run_style": "E/P"},
        {"horse": "C", "recent_early_pace": 101, "run_style": "P"},
    ]
    scenario = classify_race_pace(rows)
    assert scenario.label == "Fast"


def test_pace_map_contains_start_and_finish_positions():
    rows = [
        {"horse": "A", "program": "1", "post": "1", "run_style": "E", "recent_early_pace": 110, "recent_late_pace": 95, "proprietary_speed_figure": 95},
        {"horse": "B", "program": "2", "post": "2", "run_style": "S", "recent_early_pace": 90, "recent_late_pace": 108, "proprietary_speed_figure": 98},
    ]
    pace_map = build_pace_map(rows)
    assert len(pace_map) == 2
    assert "predicted_start_pos" in pace_map[0]
    assert "predicted_finish_pos" in pace_map[0]
