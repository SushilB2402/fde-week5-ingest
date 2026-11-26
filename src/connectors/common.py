import csv
from pathlib import Path
import pandas as pd


def count_rows(path: str, has_header: bool = True) -> int:
    with open(path, newline="", encoding="utf-8") as f:
        total = sum(1 for _ in csv.reader(f))
    if has_header and total > 0:
        return total - 1
    return total


def read_csv_chunks(
    path: str,
    *,
    names: list[str] | None = None,
    has_header: bool = True,
    chunksize: int = 50_000,
):
    row_number = 0
    read_kwargs: dict = {
        "chunksize": chunksize,
        "dtype": str,
        "encoding": "utf-8",
    }

    if names is not None:
        read_kwargs["header"] = None if not has_header else 0
        read_kwargs["names"] = names
    elif not has_header:
        read_kwargs["header"] = None

    for chunk in pd.read_csv(path, **read_kwargs):
        chunk = chunk.where(pd.notna(chunk), None)
        for row in chunk.to_dict(orient="records"):
            row_number += 1
            yield row_number, row


def ensure_parent_dir(file_path: str | Path) -> Path:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
