from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATA_DIR = Path("data")
PREDICTIONS_FILE = DATA_DIR / "predictions_store.json"
LEARNING_FILE = DATA_DIR / "learning_profile.json"


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return default


def _write_json(path: Path, payload: Any) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))


def load_predictions() -> dict[str, Any]:
    return _read_json(PREDICTIONS_FILE, {})


def save_predictions(payload: dict[str, Any]) -> None:
    _write_json(PREDICTIONS_FILE, payload)


def load_learning_profile() -> dict[str, float]:
    return _read_json(LEARNING_FILE, {})


def save_learning_profile(payload: dict[str, float]) -> None:
    _write_json(LEARNING_FILE, payload)


def record_card_predictions(track: str, card_date: str, card_predictions: list[dict[str, Any]]) -> None:
    all_data = load_predictions()
    all_data.setdefault(track, {})[card_date] = card_predictions
    save_predictions(all_data)


def get_card_predictions(track: str, card_date: str) -> list[dict[str, Any]]:
    all_data = load_predictions()
    return all_data.get(track, {}).get(card_date, [])


def learn_from_results(results_rows: list[dict[str, str]], factor_key: str = "recent_late_pace") -> dict[str, float]:
    """Simple online learning: adjust one factor bias based on hit-rate of stored winners."""
    profile = load_learning_profile()
    predictions = load_predictions()

    total = 0
    hits = 0
    for row in results_rows:
        track = row.get("track", "").strip()
        date = row.get("date", "").strip()
        race = str(row.get("race_number", "")).strip()
        winner = row.get("winner_program", "").strip() or row.get("winner_horse", "").strip()
        if not track or not date or not race or not winner:
            continue
        card = predictions.get(track, {}).get(date, [])
        pred = next((x for x in card if str(x.get("race_number", "")) == race), None)
        if not pred:
            continue
        total += 1
        predicted = str(pred.get("predicted_winner_program", "")).strip() or str(pred.get("predicted_winner_horse", "")).strip()
        if predicted and predicted.lower() == winner.lower():
            hits += 1

    if total == 0:
        return profile

    hit_rate = hits / total
    current = float(profile.get(factor_key, 1.0))
    # If underperforming, increase late pace modestly; if strong, slightly normalize.
    if hit_rate < 0.2:
        current += 0.1
    elif hit_rate > 0.4:
        current -= 0.05
    profile[factor_key] = max(0.7, min(1.4, current))
    profile["last_hit_rate"] = round(hit_rate, 4)
    save_learning_profile(profile)
    return profile
