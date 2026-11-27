import csv
import json
from pathlib import Path

from src.connectors.common import read_csv_chunks
from src.normalise import map_source2_row, map_source3_row
from src.pipeline import run_pipeline


def _write_csv(
    path: Path,
    rows: list[list[str]],
    header: list[str] | None = None,
) -> str:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if header is not None:
            writer.writerow(header)
        writer.writerows(rows)
    return str(path)


def test_pipeline_rejects_bad_rows_and_reconciles_counts(tmp_path: Path, caplog):
    reg_csv = _write_csv(
        tmp_path / "reg.csv",
        header=["CODE", "POSTCODE", "NUMBER_OF_PATIENTS"],
        rows=[
            ["A81001", "TS18 1HU", "1200"],
            ["A81002", "TS18 2AA", "-5"],
            ["A81003", "TS18 3BB", "900"],
        ],
    )
    prac_csv = _write_csv(
        tmp_path / "prac.csv",
        header=None,
        rows=[
            ["   ", "BAD PRACTICE", "TS18 1HU", "ACTIVE"],
            ["A81004", "GOOD PRACTICE", "TS18 1HU", "OPEN"],
            ["A81005", "OK PRACTICE", "TS18 1HU", "ACTIVE"],
        ],
    )

    loaded_out = tmp_path / "loaded.csv"
    rejected_out = tmp_path / "rejected.jsonl"

    registry = {
        "registrations": (
            lambda p: read_csv_chunks(p, has_header=True),
            map_source2_row,
            reg_csv,
            True,
        ),
        "epraccur": (
            lambda p: read_csv_chunks(
                p,
                names=["PRACTICE_CODE", "PRACTICE_NAME", "POSTCODE", "STATUS"],
                has_header=False,
            ),
            map_source3_row,
            prac_csv,
            False,
        ),
    }

    with caplog.at_level("INFO"):
        exit_code = run_pipeline(
            registry=registry,
            loaded_path=loaded_out,
            rejected_path=rejected_out,
        )

    assert exit_code == 0
    assert loaded_out.exists()
    assert rejected_out.exists()

    rejected_entries = [
        json.loads(line)
        for line in rejected_out.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rejected_entries) == 3

    by_key = {(e["source"], e["source_row"]): e for e in rejected_entries}

    reg_bad = by_key[("registrations", 2)]
    assert any("patient_count" in r and "-5" in r for r in reg_bad["reasons"])

    prac_blank = by_key[("epraccur", 1)]
    assert any("practice_code" in r for r in prac_blank["reasons"])

    prac_status = by_key[("epraccur", 2)]
    assert any("status" in r and "OPEN" in r for r in prac_status["reasons"])

    with open(loaded_out, newline="", encoding="utf-8") as f:
        loaded_rows = list(csv.DictReader(f))
    assert len(loaded_rows) == 3


def test_pipeline_fails_on_mid_read_error(tmp_path: Path, caplog):
    sample_csv = _write_csv(
        tmp_path / "sample.csv",
        header=["CODE", "POSTCODE", "NUMBER_OF_PATIENTS"],
        rows=[
            ["A81001", "TS18 1HU", "100"],
            ["A81002", "TS18 2AA", "200"],
        ],
    )
    loaded_out = tmp_path / "loaded.csv"
    rejected_out = tmp_path / "rejected.jsonl"

    def failing_reader(path: str):
        for row_num, row in read_csv_chunks(path, has_header=True):
            if row_num == 2:
                raise RuntimeError("Simulated mid-file read error")
            yield row_num, row

    registry = {
        "registrations": (failing_reader, map_source2_row, sample_csv, True),
    }

    with caplog.at_level("INFO"):
        exit_code = run_pipeline(
            registry=registry,
            loaded_path=loaded_out,
            rejected_path=rejected_out,
        )

    assert exit_code == 1
    assert not loaded_out.exists()
    assert "Pipeline FAILED" in caplog.text

