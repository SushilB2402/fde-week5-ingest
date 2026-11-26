"""
Week 5 ingestion pipeline.
"""

import json
import logging
import sys
from pathlib import Path
import pandas as pd
from pydantic import ValidationError

from src.connectors.common import count_rows, ensure_parent_dir
from src.connectors.source1 import read_source1
from src.connectors.source2 import read_source2
from src.connectors.source3 import read_source3
from src.normalise import (
    map_source1_row,
    map_source2_row,
    map_source3_row,
)

LOADED_CSV_PATH = Path("data/out/loaded.csv")
LOADED_STAGING_PATH = Path("data/out/.loaded.csv.tmp")
REJECTED_JSONL_PATH = Path("data/out/rejected.jsonl")
REPORTS_DIR = Path("reports")
LOAD_CHUNK_SIZE = 10_000

# (read_fn, map_fn, data_path, has_header)
CONNECTOR_REGISTRY = {
    "epd": (
        read_source1,
        map_source1_row,
        "data/raw/epd_snomed_202609.csv",
        True,
    ),
    "registrations": (
        read_source2,
        map_source2_row,
        "data/raw/gp-reg-pat-prac-all.csv",
        True,
    ),
    "epraccur": (
        read_source3,
        map_source3_row,
        "data/raw/epraccur.csv",
        False,
    ),
}

logger = logging.getLogger("pipeline")


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ensure_output_dirs() -> None:
    Path("data/out").mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def format_validation_reasons(err: ValidationError) -> list[str]:
    reasons: list[str] = []
    for item in err.errors():
        loc = item.get("loc", ())
        field = ".".join(str(part) for part in loc) if loc else "<record>"
        msg = item.get("msg", "invalid value")
        bad_value = item.get("input")
        reasons.append(f"Field '{field}' with value {bad_value!r}: {msg}")
    return reasons


def append_loaded_chunk(
    records: list[dict],
    output_path: Path,
    header_written: bool,
) -> bool:
    if not records:
        return header_written

    ensure_parent_dir(output_path)
    df = pd.DataFrame(records)
    df.to_csv(
        output_path,
        mode="a",
        index=False,
        header=not header_written,
        encoding="utf-8",
    )
    return True


def append_rejected_record(
    rejected_file,
    source: str,
    source_row: int,
    raw_row: dict,
    err: ValidationError,
) -> None:
    entry = {
        "source": source,
        "source_row": source_row,
        "reasons": format_validation_reasons(err),
        "raw_record": raw_row,
    }
    rejected_file.write(json.dumps(entry, ensure_ascii=False) + "\n")


def cleanup_files(*paths: Path) -> None:
    for path in paths:
        if path.exists():
            path.unlink()


def run_pipeline(
    registry: dict = CONNECTOR_REGISTRY,
    loaded_path: Path = LOADED_CSV_PATH,
    rejected_path: Path = REJECTED_JSONL_PATH,
) -> int:
    ensure_output_dirs()
    staging_path = loaded_path.parent / f".{loaded_path.name}.tmp"
    cleanup_files(staging_path, rejected_path)
    ensure_parent_dir(rejected_path)

    stats: dict[str, dict[str, int]] = {}
    failed_sources: set[str] = set()
    header_written = False
    pending_loaded: list[dict] = []

    with open(rejected_path, "a", encoding="utf-8") as rejected_fh:
        for source_name, (read_fn, map_fn, data_path, has_header) in registry.items():
            logger.info("Starting connector '%s' from '%s'", source_name, data_path)
            source_stats = {"read": 0, "loaded": 0, "rejected": 0}
            stats[source_name] = source_stats

            file_path = Path(data_path)
            if not file_path.exists():
                logger.error(
                    "Missing input file '%s' for connector '%s' — see docs/Sources.md",
                    data_path,
                    source_name,
                )
                failed_sources.add(source_name)
                logger.info(
                    "Skipped '%s' | read=0 loaded=0 rejected=0",
                    source_name,
                )
                continue

            expected_rows = count_rows(data_path, has_header=has_header)

            try:
                for source_row, raw_row in read_fn(data_path):
                    source_stats["read"] += 1
                    try:
                        record = map_fn(source_row, raw_row)
                        pending_loaded.append(record.model_dump())
                        source_stats["loaded"] += 1

                        if len(pending_loaded) >= LOAD_CHUNK_SIZE:
                            header_written = append_loaded_chunk(
                                pending_loaded,
                                staging_path,
                                header_written,
                            )
                            pending_loaded.clear()

                    except ValidationError as exc:
                        source_stats["rejected"] += 1
                        append_rejected_record(
                            rejected_fh,
                            source_name,
                            source_row,
                            raw_row,
                            exc,
                        )
            except Exception as exc:
                logger.error(
                    "Connector '%s' failed while reading '%s': %s",
                    source_name,
                    data_path,
                    exc,
                )
                failed_sources.add(source_name)

            if source_stats["read"] == 0:
                logger.error(
                    "Connector '%s' read 0 rows from '%s'",
                    source_name,
                    data_path,
                )
                failed_sources.add(source_name)

            if source_stats["read"] != expected_rows:
                logger.error(
                    "Row count mismatch for '%s': read=%d, expected=%d",
                    source_name,
                    source_stats["read"],
                    expected_rows,
                )
                failed_sources.add(source_name)

            accounted = source_stats["loaded"] + source_stats["rejected"]
            if source_stats["read"] != accounted:
                logger.error(
                    "Balance mismatch for '%s': read=%d, loaded+rejected=%d",
                    source_name,
                    source_stats["read"],
                    accounted,
                )
                failed_sources.add(source_name)

            logger.info(
                "Finished '%s' | read=%d loaded=%d rejected=%d",
                source_name,
                source_stats["read"],
                source_stats["loaded"],
                source_stats["rejected"],
            )

        if pending_loaded:
            header_written = append_loaded_chunk(
                pending_loaded,
                staging_path,
                header_written,
            )
            pending_loaded.clear()

    logger.info("=== Pipeline Summary ===")
    for source_name, s in stats.items():
        logger.info(
            "%-15s | read=%-7d loaded=%-7d rejected=%-7d",
            source_name,
            s["read"],
            s["loaded"],
            s["rejected"],
        )

    if failed_sources:
        cleanup_files(staging_path)
        logger.warning(
            "Outputs in '%s' may be incomplete or missing; staging file removed on failure",
            loaded_path,
        )
        logger.error(
            "Pipeline FAILED: %d source(s) could not be read or reconciled (%s)",
            len(failed_sources),
            ", ".join(sorted(failed_sources)),
        )
        return 1

    if staging_path.exists():
        staging_path.replace(loaded_path)
    return 0


def main() -> None:
    setup_logging()
    logger.info("Pipeline started")
    ensure_output_dirs()
    logger.info("Output folders ready")
    exit_code = run_pipeline()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
