import io
import zipfile

from results_zip_parser import parse_results_zip


def _zip_with_start_file() -> bytes:
    row = [""] * 99
    row[0] = "DMR"  # track
    row[1] = "20050701"  # date
    row[2] = "1"  # race
    row[4] = "Winner Horse"  # horse name
    row[8] = "1"  # program
    row[60] = "1"  # official position

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("start_file.csv", ",".join(row) + "\n")
    return buf.getvalue()


def test_parse_results_zip_extracts_winners_from_start_file():
    blob = _zip_with_start_file()
    parsed = parse_results_zip(blob, filename="DMR20050701c.zip")
    assert parsed.summary["rows_extracted"] == 1
    assert parsed.rows[0]["track"] == "DMR"
    assert parsed.rows[0]["date"] == "20050701"
    assert parsed.rows[0]["race_number"] == "1"
    assert parsed.rows[0]["winner_program"] == "1"
