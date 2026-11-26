import csv

import pandas as pd

from pydantic import ValidationError

from src.normalise import map_source2_row

def read_source2(path: str):

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

        for row in chunk.to_dict(
            orient="records"
        ):

            row_number += 1

            yield row_number, row

def count_csv_rows(path: str):

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

def validate_source2(path: str):

    rows_read = 0
    loaded = 0
    failed = 0

    expected_rows = count_csv_rows(
        path
    )

    for source_row, row in read_source2(
        path
    ):

        rows_read += 1

        try:

            map_source2_row(
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

    validate_source2(
        "data/raw/gp-reg-pat-prac-all.csv"
    )
    