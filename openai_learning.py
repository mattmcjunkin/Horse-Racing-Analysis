from __future__ import annotations

import json
import os
from typing import Any


def build_training_payload(
    factor_keys: list[str],
    stored_predictions: dict[str, Any],
    recent_results: list[dict[str, str]],
) -> dict[str, Any]:
    cards = 0
    races = 0
    for track_data in stored_predictions.values():
        if not isinstance(track_data, dict):
            continue
        for card in track_data.values():
            cards += 1
            races += len(card) if isinstance(card, list) else 0

    return {
        "factor_keys": factor_keys,
        "stored_cards": cards,
        "stored_races": races,
        "recent_results": recent_results[:500],
        "instruction": "Return JSON object with per-factor multipliers between 0.7 and 1.4.",
        "output_schema": {"<factor_key>": 1.0},
    }


def parse_multiplier_response(raw: str, factor_keys: list[str]) -> dict[str, float]:
    payload = json.loads(raw)
    out: dict[str, float] = {}
    for key in factor_keys:
        if key in payload:
            try:
                out[key] = max(0.7, min(1.4, float(payload[key])))
            except (TypeError, ValueError):
                continue
    return out


def suggest_learning_multipliers(
    factor_keys: list[str],
    stored_predictions: dict[str, Any],
    recent_results: list[dict[str, str]],
    api_key: str | None = None,
    model: str = "gpt-4o-mini",
) -> tuple[dict[str, float], str]:
    key = api_key or os.getenv("OPENAI_API_KEY", "")
    if not key:
        return {}, "Missing OpenAI API key."

    try:
        from openai import OpenAI
    except ImportError:
        return {}, "openai package is not installed."

    prompt_payload = build_training_payload(factor_keys, stored_predictions, recent_results)

    client = OpenAI(api_key=key)
    try:
        response = client.responses.create(
            model=model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You optimize horse-racing factor multipliers based on prediction outcomes. "
                        "Output ONLY valid JSON object."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(prompt_payload),
                },
            ],
            temperature=0.1,
        )
        raw = response.output_text.strip()
        multipliers = parse_multiplier_response(raw, factor_keys)
        if not multipliers:
            return {}, "OpenAI returned no valid multipliers."
        return multipliers, "ok"
    except Exception as exc:  # noqa: BLE001
        return {}, f"OpenAI request failed: {exc}"
