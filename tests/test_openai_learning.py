from openai_learning import build_training_payload, parse_multiplier_response


def test_build_training_payload_counts_cards_and_races():
    stored = {"GP": {"20250101": [{"race_number": 1}, {"race_number": 2}]}, "SA": {"20250102": [{"race_number": 1}]}}
    payload = build_training_payload(["prime_power"], stored, [{"track": "GP"}])
    assert payload["stored_cards"] == 2
    assert payload["stored_races"] == 3


def test_parse_multiplier_response_clamps_and_filters():
    raw = '{"prime_power": 1.8, "recent_late_pace": 0.65, "junk": 9}'
    parsed = parse_multiplier_response(raw, ["prime_power", "recent_late_pace"])
    assert parsed["prime_power"] == 1.4
    assert parsed["recent_late_pace"] == 0.7
    assert "junk" not in parsed
