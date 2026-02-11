from __future__ import annotations

from typing import Dict


def detect_surface(surface_code: str) -> str:
    code = (surface_code or "").strip()
    if not code:
        return "unknown"
    if code in {"T", "t"}:
        return "turf"
    if code in {"D", "d"}:
        return "dirt"
    return "other"


def recommended_weights(factor_keys: list[str], surface: str, pace_scenario: str, learning_profile: Dict[str, float] | None = None) -> Dict[str, float]:
    weights = {k: 1.0 for k in factor_keys}

    # Surface-driven adjustments
    if surface == "turf":
        weights["best_speed_turf"] = 1.6
        weights["recent_late_pace"] = 1.4
        weights["jockey_win_pct"] = 1.2
        weights["best_speed_fast"] = 0.8
        weights["best_speed_off"] = 0.7
    elif surface == "dirt":
        weights["best_speed_fast"] = 1.5
        weights["recent_early_pace"] = 1.25
        weights["prime_power"] = 1.2
        weights["best_speed_turf"] = 0.7
    else:
        weights["best_speed_off"] = 1.35
        weights["track_win_pct"] = 1.2

    # Pace-scenario-driven adjustments
    pace = (pace_scenario or "").lower()
    if pace == "fast":
        weights["recent_late_pace"] = max(weights.get("recent_late_pace", 1.0), 1.55)
        weights["recent_early_pace"] = min(weights.get("recent_early_pace", 1.0), 0.9)
        weights["days_since_last"] = min(weights.get("days_since_last", 1.0), 0.9)
    elif pace == "slow":
        weights["recent_early_pace"] = max(weights.get("recent_early_pace", 1.0), 1.55)
        weights["pace_par_avg"] = max(weights.get("pace_par_avg", 1.0), 1.3)
        weights["recent_late_pace"] = min(weights.get("recent_late_pace", 1.0), 0.95)
    else:
        weights["pace_par_avg"] = max(weights.get("pace_par_avg", 1.0), 1.15)

    # Apply learning multipliers (if any)
    learning_profile = learning_profile or {}
    for key, mult in learning_profile.items():
        if key in weights:
            weights[key] = float(weights[key]) * float(mult)

    # Clamp to slider range
    for k, v in list(weights.items()):
        weights[k] = max(0.0, min(2.0, float(v)))

    return weights
