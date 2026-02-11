from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from brisnet_parser import HorseRecord


@dataclass(frozen=True)
class Factor:
    key: str
    label: str
    extractor: Callable[[HorseRecord], float]
    higher_is_better: bool = True


DEFAULT_FACTORS = [
    Factor("prime_power", "BRIS Prime Power (#251)", lambda r: r.get_num(251, 0.0)),
    Factor("best_speed_life", "Best BRIS Speed - Life (#1328)", lambda r: r.get_num(1328, 0.0)),
    Factor("best_speed_fast", "Best BRIS Speed - Fast Track (#1178)", lambda r: r.get_num(1178, 0.0)),
    Factor("best_speed_turf", "Best BRIS Speed - Turf (#1179)", lambda r: r.get_num(1179, 0.0)),
    Factor("best_speed_off", "Best BRIS Speed - Off Track (#1180)", lambda r: r.get_num(1180, 0.0)),
    Factor("best_speed_distance", "Best BRIS Speed - Distance (#1181)", lambda r: r.get_num(1181, 0.0)),
    Factor("speed_par", "BRIS Speed Par for Class (#217)", lambda r: r.get_num(217, 0.0)),
    Factor("pace_par_avg", "Pace Par Avg (2f/4f/6f #214-216)", lambda r: _avg([r.get_num(214), r.get_num(215), r.get_num(216)])),
    Factor("recent_early_pace", "Recent Early Pace Avg (2f/4f/6f)", lambda r: _recent_early_pace_avg(r)),
    Factor("recent_late_pace", "Recent Late Pace Avg", lambda r: _recent_late_pace_avg(r)),
    Factor("days_since_last", "Days Since Last Race (#224)", lambda r: r.get_num(224, 999.0), higher_is_better=False),
    Factor("trainer_win_pct", "Trainer Win % (Current Meet)", lambda r: _safe_pct(r.get_num(30), r.get_num(29))),
    Factor("jockey_win_pct", "Jockey Win % (Current Meet)", lambda r: _safe_pct(r.get_num(36), r.get_num(35))),
    Factor("distance_win_pct", "Win % at Today's Distance", lambda r: _safe_pct(r.get_num(66), r.get_num(65))),
    Factor("track_win_pct", "Win % at Today's Track", lambda r: _safe_pct(r.get_num(71), r.get_num(70))),
    Factor("recent_speed_avg", "Avg Last-3 BRIS Speed Ratings", lambda r: _recent_speed_avg(r)),
]


def _avg(values: list[float]) -> float:
    clean = [v for v in values if v > 0]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0


def _recent_speed_avg(record: HorseRecord) -> float:
    ratings = [record.get_num(field, 0.0) for field in range(846, 856)]
    return _avg(ratings[:3] if any(ratings[:3]) else ratings)


def _recent_early_pace_avg(record: HorseRecord) -> float:
    values: list[float] = []
    for i in range(3):
        values.extend([
            record.get_num(766 + i, 0.0),
            record.get_num(776 + i, 0.0),
            record.get_num(786 + i, 0.0),
        ])
    return _avg(values)


def _recent_late_pace_avg(record: HorseRecord) -> float:
    values = [record.get_num(816 + i, 0.0) for i in range(3)]
    return _avg(values)


def _bris_baseline(record: HorseRecord) -> float:
    # Prefer most-recent BRIS speed (#846). Fallback to recent average.
    latest = record.get_num(846, 0.0)
    if latest > 0:
        return latest
    return _recent_speed_avg(record)


def compute_scores(records: list[HorseRecord], weights: dict[str, float], adjustment_scale: float = 12.0) -> list[dict]:
    rows: list[dict] = []
    for record in records:
        row = {
            "horse": record.horse_name,
            "trainer": record.trainer,
            "jockey": record.jockey,
            "post": record.get_text(4),
            "program": record.get_text(43),
            "bris_speed_figure": _bris_baseline(record),
        }
        for factor in DEFAULT_FACTORS:
            row[factor.key] = factor.extractor(record)
        rows.append(row)

    if not rows:
        return rows

    for factor in DEFAULT_FACTORS:
        values = [float(r[factor.key]) for r in rows]
        min_v, max_v = min(values), max(values)
        for row in rows:
            val = float(row[factor.key])
            if max_v == min_v:
                normalized = 50.0
            else:
                normalized = (val - min_v) / (max_v - min_v) * 100.0
            if not factor.higher_is_better:
                normalized = 100.0 - normalized
            row[f"{factor.key}_normalized"] = normalized

    for row in rows:
        contributions: dict[str, float] = {}
        weighted_delta = 0.0
        for factor in DEFAULT_FACTORS:
            weight = weights.get(factor.key, 0.0)
            centered = (row[f"{factor.key}_normalized"] - 50.0) / 50.0
            contribution = centered * weight
            contributions[factor.key] = contribution
            weighted_delta += contribution

        figure_adjustment = weighted_delta * adjustment_scale
        proprietary_figure = row["bris_speed_figure"] + figure_adjustment

        row["weighted_delta"] = weighted_delta
        row["figure_adjustment"] = figure_adjustment
        row["proprietary_speed_figure"] = proprietary_figure
        row["figure_delta_vs_bris"] = figure_adjustment
        row["factor_contributions"] = contributions
        row["proprietary_score"] = proprietary_figure

    rows.sort(key=lambda x: x["proprietary_speed_figure"], reverse=True)
    return rows
