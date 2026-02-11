from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ParsedResultsBundle:
    rows: list[dict[str, str]]
    summary: dict[str, Any]


def _parse_csv_text(text: str) -> list[list[str]]:
    reader = csv.reader(io.StringIO(text))
    return [row for row in reader if row]


def _safe_get(row: list[str], idx_1: int) -> str:
    i = idx_1 - 1
    if i < 0 or i >= len(row):
        return ""
    return (row[i] or "").strip()


def _is_headerish(row: list[str]) -> bool:
    cell = (row[0] if row else "").lower()
    return "track" in cell or "field" in cell or cell.startswith("#")


def _parse_start_file(rows: list[list[str]]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        if not row or _is_headerish(row):
            continue
        official_pos = _safe_get(row, 61)
        if official_pos != "1":
            continue
        out.append(
            {
                "track": _safe_get(row, 1),
                "date": _safe_get(row, 2),
                "race_number": _safe_get(row, 3),
                "winner_program": _safe_get(row, 9),
                "winner_horse": _safe_get(row, 5),
                "source": "start_file",
            }
        )
    return out


def _parse_itm_file(rows: list[list[str]]) -> list[dict[str, str]]:
    out: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in rows:
        if not row or _is_headerish(row):
            continue
        win_payoff = _safe_get(row, 9)
        if not win_payoff:
            continue
        try:
            if float(win_payoff) <= 0:
                continue
        except ValueError:
            continue
        key = (_safe_get(row, 1), _safe_get(row, 2), _safe_get(row, 3))
        out[key] = {
            "track": key[0],
            "date": key[1],
            "race_number": key[2],
            "winner_program": _safe_get(row, 8),
            "winner_horse": _safe_get(row, 5),
            "source": "itm_file",
        }
    return list(out.values())


def parse_results_zip(zip_bytes: bytes, filename: str = "") -> ParsedResultsBundle:
    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = zf.namelist()

    all_rows: list[dict[str, str]] = []
    found_files: dict[str, int] = {"start": 0, "itm": 0}

    for name in names:
        lowered = Path(name).name.lower()
        if not lowered.endswith((".txt", ".csv", ".dat")):
            continue
        text = zf.read(name).decode("utf-8", errors="ignore")
        rows = _parse_csv_text(text)

        # File type inference by field count + naming hints
        if "start" in lowered or any(len(r) >= 61 for r in rows[:5]):
            parsed = _parse_start_file(rows)
            if parsed:
                found_files["start"] += 1
                all_rows.extend(parsed)
                continue

        if "itm" in lowered or "payoff" in lowered or any(len(r) >= 10 for r in rows[:5]):
            parsed = _parse_itm_file(rows)
            if parsed:
                found_files["itm"] += 1
                all_rows.extend(parsed)

    # de-dup by track/date/race preferring start file rows
    dedup: dict[tuple[str, str, str], dict[str, str]] = {}
    for row in all_rows:
        key = (row.get("track", ""), row.get("date", ""), row.get("race_number", ""))
        if key not in dedup or row.get("source") == "start_file":
            dedup[key] = row

    base = Path(filename).name
    m = re.match(r"([A-Za-z]{2,4})(\d{8})", base)
    guessed = {"track": m.group(1).upper(), "date": m.group(2)} if m else {}

    summary = {
        "zip_name": base,
        "files_in_zip": len(names),
        "rows_extracted": len(dedup),
        "file_types_detected": found_files,
        "guessed_card": guessed,
    }
    return ParsedResultsBundle(rows=list(dedup.values()), summary=summary)
