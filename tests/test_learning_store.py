import learning_store


def _patch_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(learning_store, "DATA_DIR", tmp_path)
    monkeypatch.setattr(learning_store, "PREDICTIONS_FILE", tmp_path / "predictions_store.json")
    monkeypatch.setattr(learning_store, "RESULTS_FILE", tmp_path / "results_store.json")
    monkeypatch.setattr(learning_store, "LEARNING_FILE", tmp_path / "learning_profile.json")


def test_record_and_fetch_predictions(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    payload = [{"race_number": 1, "predicted_winner_program": "2"}]
    learning_store.record_card_predictions("GP", "20250101", payload)
    got = learning_store.get_card_predictions("GP", "20250101")
    assert isinstance(got, list)
    assert got[0]["race_number"] == 1


def test_record_results_and_compare(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    learning_store.record_card_predictions(
        "GP",
        "20250101",
        [{"race_number": 1, "predicted_winner_program": "2", "predicted_winner_horse": "Horse A"}],
    )
    learning_store.record_results_rows(
        [{"track": "GP", "date": "20250101", "race_number": "1", "winner_program": "2"}]
    )
    cmp_rows = learning_store.compare_card_predictions_to_results("GP", "20250101")
    assert len(cmp_rows) == 1
    assert cmp_rows[0]["match"] is True


def test_learn_from_results_returns_profile_dict(tmp_path, monkeypatch):
    _patch_paths(tmp_path, monkeypatch)
    learning_store.record_card_predictions("GP", "20250101", [{"race_number": 1, "predicted_winner_program": "2"}])
    results = [{"track": "GP", "date": "20250101", "race_number": "1", "winner_program": "2"}]
    profile = learning_store.learn_from_results(results)
    assert isinstance(profile, dict)
    assert "last_hit_rate" in profile
