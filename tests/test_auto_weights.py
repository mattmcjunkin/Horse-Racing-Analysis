from auto_weights import detect_surface, recommended_weights


def test_detect_surface_codes():
    assert detect_surface("T") == "turf"
    assert detect_surface("d") == "dirt"
    assert detect_surface("A") == "other"


def test_recommended_weights_shift_for_turf_fast():
    keys = [
        "best_speed_turf",
        "best_speed_fast",
        "recent_late_pace",
        "recent_early_pace",
        "pace_par_avg",
    ]
    w = recommended_weights(keys, surface="turf", pace_scenario="Fast")
    assert w["best_speed_turf"] > w["best_speed_fast"]
    assert w["recent_late_pace"] >= 1.5
    assert w["recent_early_pace"] <= 1.0
