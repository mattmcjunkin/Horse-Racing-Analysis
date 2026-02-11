from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from typing import Iterable, List

MAX_FIELDS = 1435


@dataclass
class HorseRecord:
    """Represents one horse row normalized to BRIS-like field numbers."""

    fields: List[str]

    def get_raw(self, field_number: int) -> str:
        if field_number < 1 or field_number > len(self.fields):
            return ""
        return self.fields[field_number - 1].strip()

    def get_text(self, field_number: int, default: str = "") -> str:
        value = self.get_raw(field_number)
        return value if value else default

    def get_num(self, field_number: int, default: float = 0.0) -> float:
        value = self.get_raw(field_number)
        if not value:
            return default
        try:
            return float(value)
        except ValueError:
            return default

    @property
    def track(self) -> str:
        return self.get_text(1, "UNK")

    @property
    def date(self) -> str:
        return self.get_text(2, "00000000")

    @property
    def race_number(self) -> int:
        return int(self.get_num(3, 0))

    @property
    def horse_name(self) -> str:
        return self.get_text(45, "Unknown Horse")

    @property
    def trainer(self) -> str:
        return self.get_text(28)

    @property
    def jockey(self) -> str:
        return self.get_text(33)


def _normalize_fields(parsed: list[str]) -> list[str]:
    if len(parsed) < MAX_FIELDS:
        parsed.extend([""] * (MAX_FIELDS - len(parsed)))
    elif len(parsed) > MAX_FIELDS:
        parsed = parsed[:MAX_FIELDS]
    return parsed


def parse_single_file_line(line: str) -> HorseRecord:
    reader = csv.reader(StringIO(line), delimiter=",", quotechar='"')
    return HorseRecord(fields=_normalize_fields(next(reader)))


def parse_single_file_content(content: str) -> List[HorseRecord]:
    lines = [ln for ln in content.splitlines() if ln.strip()]
    return [parse_single_file_line(line) for line in lines]


def parse_drf_content(content: str) -> List[HorseRecord]:
    """Parse DRF CSV/TSV/pipe files by mapping named columns into BRIS-style indexes."""
    lines = [ln for ln in content.splitlines() if ln.strip()]
    if not lines:
        return []

    sample = "\n".join(lines[:5])
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",|\t;")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ","

    reader = csv.DictReader(StringIO("\n".join(lines)), delimiter=delimiter)
    records: list[HorseRecord] = []

    col_map = {
        "track": 1,
        "race_date": 2,
        "date": 2,
        "race": 3,
        "race_number": 3,
        "post": 4,
        "post_position": 4,
        "trainer": 28,
        "jockey": 33,
        "program": 43,
        "horse": 45,
        "horse_name": 45,
        "prime_power": 251,
        "speed_par": 217,
        "days_since_last": 224,
        "best_speed_life": 1328,
        "best_speed_fast": 1178,
        "best_speed_turf": 1179,
        "best_speed_off": 1180,
        "best_speed_distance": 1181,
        "pace_2f": 766,
        "pace_4f": 776,
        "pace_6f": 786,
        "late_pace": 816,
        "bris_speed": 846,
    }

    for row in reader:
        fields = [""] * MAX_FIELDS
        normalized = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
        for col, field_no in col_map.items():
            if col in normalized and normalized[col] != "":
                fields[field_no - 1] = normalized[col]
        records.append(HorseRecord(fields=fields))

    return records


def parse_content(content: str, source_format: str = "auto") -> List[HorseRecord]:
    if source_format == "brisnet":
        return parse_single_file_content(content)
    if source_format == "drf":
        return parse_drf_content(content)

    first_line = next((ln for ln in content.splitlines() if ln.strip()), "")
    if first_line.count(",") > 100:
        return parse_single_file_content(content)
    return parse_drf_content(content)


def group_by_race(records: Iterable[HorseRecord]) -> dict[tuple[str, str, int], list[HorseRecord]]:
    races: dict[tuple[str, str, int], list[HorseRecord]] = {}
    for record in records:
        key = (record.track, record.date, record.race_number)
        races.setdefault(key, []).append(record)
    return races
