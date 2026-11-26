import csv

import pandas as pd

from pydantic import ValidationError

from src.normalise import map_source1_row

def read_source1(path: str):
    """
    Yield (source_row, raw_dict) pairs from Source 1.

    Uses chunked reading to support large files.
    """

    row_number = 0

    for chunk in pd.read_csv(
        path,
        chunksize=50_000,
        dtype=str,
        encoding="utf-8",
    ):

        chunk = chunk.where(
            pd.notna(chunk),
            None,
        )

        records = chunk.to_dict(
            orient="records"
        )

        for row in records:

            row_number += 1

            yield row_number, row

def count_csv_rows(path: str) -> int:
    """
    Independent row count.

    Uses csv.reader rather than line counting so
    quoted embedded newlines are handled correctly.
    """

    with open(
        path,
        newline="",
        encoding="utf-8",
    ) as f:

        return (
            sum(
                1
                for _ in csv.reader(f)
            )
            - 1
        )

def validate_source1(path: str):

    rows_read = 0
    loaded = 0
    failed = 0

    expected_rows = count_csv_rows(
        path
    )

    for source_row, row in read_source1(
        path
    ):

        rows_read += 1

        try:

            map_source1_row(
                source_row,
                row,
            )

            loaded += 1

        except ValidationError:

            failed += 1

    print(
        f"Expected Rows : {expected_rows}"
    )

    print(
        f"Rows Read     : {rows_read}"
    )

    print(
        f"Loaded        : {loaded}"
    )

    print(
        f"Failed        : {failed}"
    )

    print(
        f"Balanced      : {rows_read == loaded + failed}"
    )

    print(
        f"Reconciled    : {rows_read == expected_rows}"
    )

if __name__ == "__main__":

    validate_source1(
        "data/raw/epd_snomed_202609.csv"
    )
