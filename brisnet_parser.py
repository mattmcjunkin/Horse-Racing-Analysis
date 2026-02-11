from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from typing import Iterable, List

MAX_FIELDS = 1435


@dataclass
class HorseRecord:
    """Represents one horse line from the BRISNET Single File format."""

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
        return self.get_text(1)

    @property
    def date(self) -> str:
        return self.get_text(2)

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


def parse_single_file_line(line: str) -> HorseRecord:
    """Parse one comma-delimited BRISNET PP line into a HorseRecord."""
    reader = csv.reader(StringIO(line), delimiter=",", quotechar='"')
    parsed = next(reader)
    if len(parsed) < MAX_FIELDS:
        parsed.extend([""] * (MAX_FIELDS - len(parsed)))
    elif len(parsed) > MAX_FIELDS:
        parsed = parsed[:MAX_FIELDS]
    return HorseRecord(fields=parsed)


def parse_single_file_content(content: str) -> List[HorseRecord]:
    lines = [ln for ln in content.splitlines() if ln.strip()]
    return [parse_single_file_line(line) for line in lines]


def group_by_race(records: Iterable[HorseRecord]) -> dict[tuple[str, str, int], list[HorseRecord]]:
    races: dict[tuple[str, str, int], list[HorseRecord]] = {}
    for record in records:
        key = (record.track, record.date, record.race_number)
        races.setdefault(key, []).append(record)
    return races
