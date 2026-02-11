import learning_store


def test_record_and_fetch_predictions(tmp_path, monkeypatch):
    monkeypatch.setattr(learning_store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(learning_store, "PREDICTIONS_FILE", tmp_path / "predictions_store.json")
    monkeypatch.setattr(learning_store, "LEARNING_FILE", tmp_path / "learning_profile.json")

    payload = [{"race_number": 1, "predicted_winner_program": "2"}]
    learning_store.record_card_predictions("GP", "20250101", payload)
    got = learning_store.get_card_predictions("GP", "20250101")
    assert isinstance(got, list)
    assert got[0]["race_number"] == 1


def test_learn_from_results_returns_profile_dict(tmp_path, monkeypatch):
    monkeypatch.setattr(learning_store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(learning_store, "PREDICTIONS_FILE", tmp_path / "predictions_store.json")
    monkeypatch.setattr(learning_store, "LEARNING_FILE", tmp_path / "learning_profile.json")

    learning_store.record_card_predictions("GP", "20250101", [{"race_number": 1, "predicted_winner_program": "2"}])
    results = [{"track": "GP", "date": "20250101", "race_number": "1", "winner_program": "2"}]
    profile = learning_store.learn_from_results(results)
    assert isinstance(profile, dict)
    assert "last_hit_rate" in profile
