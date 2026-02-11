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
    Factor("days_since_last", "Days Since Last Race (#224)", lambda r: r.get_num(224, 999.0), higher_is_better=False),
    Factor("trainer_win_pct", "Trainer Win % (Current Meet)", lambda r: _safe_pct(r.get_num(30), r.get_num(29))),
    Factor("jockey_win_pct", "Jockey Win % (Current Meet)", lambda r: _safe_pct(r.get_num(36), r.get_num(35))),
    Factor("distance_win_pct", "Win % at Today's Distance", lambda r: _safe_pct(r.get_num(66), r.get_num(65))),
    Factor("track_win_pct", "Win % at Today's Track", lambda r: _safe_pct(r.get_num(71), r.get_num(70))),
    Factor("recent_speed_avg", "Avg Last-3 BRIS Speed Ratings", lambda r: _recent_speed_avg(r)),
]


def _safe_pct(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return (numerator / denominator) * 100.0


def _recent_speed_avg(record: HorseRecord) -> float:
    ratings = [record.get_num(field, 0.0) for field in range(846, 856)]
    non_zero = [x for x in ratings if x > 0]
    if not non_zero:
        return 0.0
    return sum(non_zero[:3]) / min(3, len(non_zero))


def compute_scores(records: list[HorseRecord], weights: dict[str, float]) -> list[dict]:
    rows: list[dict] = []
    for record in records:
        row = {
            "horse": record.horse_name,
            "trainer": record.trainer,
            "jockey": record.jockey,
            "post": record.get_text(4),
            "program": record.get_text(43),
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
        row["proprietary_score"] = sum(
            row[f"{factor.key}_normalized"] * weights.get(factor.key, 0.0)
            for factor in DEFAULT_FACTORS
        )

    rows.sort(key=lambda x: x["proprietary_score"], reverse=True)
    return rows
