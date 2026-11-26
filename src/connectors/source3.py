import csv
import pandas as pd
from pydantic import ValidationError
from src.normalise import map_source3_row, normalise_text

# Generic names for all 27 columns
COLUMN_NAMES = [f"COL_{i}" for i in range(27)]

# Rename only the fields we currently need
COLUMN_NAMES[0] = "PRACTICE_CODE"
COLUMN_NAMES[1] = "PRACTICE_NAME"
COLUMN_NAMES[9] = "POSTCODE"
COLUMN_NAMES[12] = "STATUS"


def read_source3(path: str):
    row_number = 0

    for chunk in pd.read_csv(
        path,
        header=None,
        names=COLUMN_NAMES,
        chunksize=50_000,
        dtype=str,
        encoding="utf-8",
    ):
        chunk = chunk.where(pd.notna(chunk), None)

        for row in chunk.to_dict(orient="records"):
            row_number += 1
            yield row_number, row


def load_practice_lookup(path: str) -> dict[str, str | None]:
    practices: dict[str, str | None] = {}

    for _, row in read_source3(path):
        code = normalise_text(row.get("PRACTICE_CODE"))
        if code:
            practices[code] = normalise_text(row.get("STATUS"))

    return practices


def count_csv_rows(path: str) -> int:
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.reader(f))


def validate_source3(path: str):
    rows_read = 0
    loaded = 0
    failed = 0
    sample_printed = False

    expected_rows = count_csv_rows(path)

    for source_row, row in read_source3(path):
        if not sample_printed:
            print(f"Sample Raw Row: {row}")
            sample_printed = True

        rows_read += 1

        try:
            map_source3_row(source_row, row)
            loaded += 1
        except ValidationError:
            failed += 1

    print(f"Expected Rows : {expected_rows}")
    print(f"Rows Read     : {rows_read}")
    print(f"Loaded        : {loaded}")
    print(f"Failed        : {failed}")
    print(f"Balanced      : {rows_read == loaded + failed}")
    print(f"Reconciled    : {rows_read == expected_rows}")


if __name__ == "__main__":
    validate_source3("data/raw/epraccur.csv")
    