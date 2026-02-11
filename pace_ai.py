from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PaceScenario:
    label: str
    confidence: float
    reason: str


def _norm(values: list[float], value: float) -> float:
    if not values:
        return 0.5
    lo, hi = min(values), max(values)
    if hi == lo:
        return 0.5
    return (value - lo) / (hi - lo)


def _run_style_speed_bonus(run_style: str) -> float:
    style = (run_style or "").upper()
    if style.startswith("E"):
        return 1.0
    if style.startswith("P"):
        return 0.4
    if style.startswith("S"):
        return -0.6
    return 0.0


def classify_race_pace(rows: list[dict[str, Any]]) -> PaceScenario:
    if not rows:
        return PaceScenario("Unknown", 0.0, "No horses loaded.")

    early_values = [float(r.get("recent_early_pace", 0.0)) for r in rows]
    avg_early = sum(early_values) / len(early_values)
    pressure = 0.0
    for r in rows:
        style_bonus = _run_style_speed_bonus(str(r.get("run_style", "")))
        pressure += _norm(early_values, float(r.get("recent_early_pace", 0.0))) + style_bonus
    pressure /= max(len(rows), 1)

    if pressure >= 0.9 or avg_early >= 102:
        return PaceScenario("Fast", min(0.95, 0.55 + pressure / 2), "Multiple horses project aggressive early speed.")
    if pressure <= 0.45 or avg_early <= 92:
        return PaceScenario("Slow", min(0.95, 0.55 + (1.0 - pressure) / 2), "Limited early pressure suggests controlled fractions.")
    return PaceScenario("Moderate", 0.65, "Balanced mix of pace pressure and running styles.")


def build_pace_map(rows: list[dict[str, Any]], top_n: int = 8) -> list[dict[str, Any]]:
    if not rows:
        return []

    early_values = [float(r.get("recent_early_pace", 0.0)) for r in rows]
    late_values = [float(r.get("recent_late_pace", 0.0)) for r in rows]
    figure_values = [float(r.get("proprietary_speed_figure", 0.0)) for r in rows]

    enriched: list[dict[str, Any]] = []
    for r in rows:
        early = _norm(early_values, float(r.get("recent_early_pace", 0.0)))
        late = _norm(late_values, float(r.get("recent_late_pace", 0.0)))
        fig = _norm(figure_values, float(r.get("proprietary_speed_figure", 0.0)))
        style_bonus = _run_style_speed_bonus(str(r.get("run_style", "")))

        start_drive = early + 0.2 * style_bonus
        finish_drive = 0.55 * fig + 0.35 * late + 0.10 * early

        row = dict(r)
        row["_start_drive"] = start_drive
        row["_finish_drive"] = finish_drive
        enriched.append(row)

    start_sorted = sorted(enriched, key=lambda x: x["_start_drive"], reverse=True)
    finish_sorted = sorted(enriched, key=lambda x: x["_finish_drive"], reverse=True)

    start_rank = {r["horse"]: i + 1 for i, r in enumerate(start_sorted)}
    finish_rank = {r["horse"]: i + 1 for i, r in enumerate(finish_sorted)}

    mapped = []
    for r in finish_sorted[:top_n]:
        mapped.append(
            {
                "horse": r.get("horse", "Unknown"),
                "program": r.get("program", ""),
                "post": r.get("post", ""),
                "run_style": r.get("run_style", ""),
                "predicted_start_pos": start_rank.get(r.get("horse", ""), 0),
                "predicted_finish_pos": finish_rank.get(r.get("horse", ""), 0),
                "early_pace": float(r.get("recent_early_pace", 0.0)),
                "late_pace": float(r.get("recent_late_pace", 0.0)),
                "proprietary_speed_figure": float(r.get("proprietary_speed_figure", 0.0)),
            }
        )
    return mapped
