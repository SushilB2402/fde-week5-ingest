"""
Data quality rule runner for Week 5 loaded output.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import pandas as pd

LOADED_CSV_PATH = Path("data/out/loaded.csv")
DEFAULT_CHUNK_SIZE = 50_000
UK_POSTCODE_RE = re.compile(r"^[A-Z]{1,2}[0-9][0-9A-Z]?\s*[0-9][A-Z]{2}$")

SOURCE_BASELINES: dict[str, int] = {
    "epd": 63_839,
    "registrations": 6_128,
    "epraccur": 15_717,
}

logger = logging.getLogger("quality")


@dataclass
class RuleResult:
    id: str
    name: str
    severity: str  # "error" or "warning"
    passed: bool
    failed_count: int
    total: int
    samples: list[dict] = field(default_factory=list)


RuleFn = Callable[[pd.DataFrame], RuleResult]


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        force=True,
    )


def prepare_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise string columns and turn whitespace/empty strings into NaN
    so null checks and string operations behave predictably.
    """
    out = df.copy()
    for col in out.columns:
        if out[col].dtype == object or pd.api.types.is_string_dtype(out[col]):
            cleaned = out[col].astype(str).str.strip()
            cleaned = cleaned.where(out[col].notna() & (cleaned != ""), other=pd.NA)
            out[col] = cleaned.astype(object)
    return out


def _sample_rows(df: pd.DataFrame, mask: pd.Series, limit: int = 5) -> list[dict]:
    if mask.empty or not mask.any():
        return []
    cols = [
        c
        for c in [
            "source",
            "source_row",
            "practice_code",
            "postcode",
            "status",
            "patient_count",
            "quantity",
            "actual_cost",
            "snomed_code",
        ]
        if c in df.columns
    ]
    sample_df = df.loc[mask, cols or df.columns].head(limit)
    return sample_df.where(sample_df.notna(), None).to_dict(orient="records")


def _make_result(
    rule_id: str,
    name: str,
    severity: str,
    df: pd.DataFrame,
    failed_mask: pd.Series,
    *,
    force_fail: bool = False,
) -> RuleResult:
    failed_count = int(failed_mask.sum()) if len(failed_mask) else 0
    passed = (failed_count == 0) and (not force_fail)
    return RuleResult(
        id=rule_id,
        name=name,
        severity=severity,
        passed=passed,
        failed_count=failed_count,
        total=int(len(df)),
        samples=_sample_rows(df, failed_mask),
    )


def rule_qr01_active_postcode(df: pd.DataFrame) -> RuleResult:
    epr = df[df["source"] == "epraccur"]
    mask = (epr["status"] == "ACTIVE") & epr["postcode"].isna()
    return _make_result(
        "QR-01",
        "Active practice missing postcode",
        "error",
        epr,
        mask,
    )


def rule_qr02_epd_metrics_and_snomed(df: pd.DataFrame) -> RuleResult:
    epd = df[df["source"] == "epd"]
    missing_metrics = epd["quantity"].isna() | epd["actual_cost"].isna()
    snomed_null_rate = float(epd["snomed_code"].isna().mean()) if len(epd) else 0.0
    snomed_breach = snomed_null_rate >= 0.01
    result = _make_result(
        "QR-02",
        "EPD missing quantity/cost or high SNOMED null rate",
        "error",
        epd,
        missing_metrics,
        force_fail=snomed_breach,
    )
    if snomed_breach and int(missing_metrics.sum()) == 0:
        # Count rows missing snomed_code as the reported metric when snomed rate breaches threshold
        snomed_mask = epd["snomed_code"].isna()
        result.failed_count = int(snomed_mask.sum())
        result.samples = _sample_rows(epd, snomed_mask)
    return result


def rule_qr03_epraccur_unique_code(df: pd.DataFrame) -> RuleResult:
    epr = df[df["source"] == "epraccur"]
    mask = epr.duplicated(subset=["practice_code"], keep=False)
    return _make_result(
        "QR-03",
        "Duplicate practice_code in EPRACCUR",
        "error",
        epr,
        mask,
    )


def rule_qr04_registrations_unique_code(df: pd.DataFrame) -> RuleResult:
    reg = df[df["source"] == "registrations"]
    mask = reg.duplicated(subset=["practice_code"], keep=False)
    return _make_result(
        "QR-04",
        "Duplicate practice_code in registrations",
        "error",
        reg,
        mask,
    )


def rule_qr05_patient_count_range(df: pd.DataFrame) -> RuleResult:
    reg = df[df["source"] == "registrations"]
    counts = pd.to_numeric(reg["patient_count"], errors="coerce")
    mask = counts.isna() | (~counts.between(1, 100_000, inclusive="both"))
    return _make_result(
        "QR-05",
        "Patient count outside 1..100,000",
        "error",
        reg,
        mask,
    )


def rule_qr06_epd_quantity_and_cost_range(df: pd.DataFrame) -> RuleResult:
    epd = df[df["source"] == "epd"]
    qty = pd.to_numeric(epd["quantity"], errors="coerce")
    cost = pd.to_numeric(epd["actual_cost"], errors="coerce")
    mask = qty.isna() | (qty <= 0) | cost.isna() | (cost < 0.01)
    return _make_result(
        "QR-06",
        "EPD quantity <= 0 or actual_cost < 0.01",
        "error",
        epd,
        mask,
    )


def rule_qr07_uk_postcode_format(df: pd.DataFrame) -> RuleResult:
    present = df[df["postcode"].notna()]
    valid_fmt = present["postcode"].astype(str).str.upper().str.match(UK_POSTCODE_RE)
    mask = ~valid_fmt
    return _make_result(
        "QR-07",
        "Postcode fails UK postcode format",
        "error",
        present,
        mask,
    )


def build_epraccur_reference_set(df: pd.DataFrame) -> set[str]:
    epr = df[df["source"] == "epraccur"]
    return set(epr["practice_code"].dropna().astype(str))


def make_qr08_referential_rule(reference_codes: set[str]) -> RuleFn:
    def rule_qr08_practice_in_epraccur(df: pd.DataFrame) -> RuleResult:
        non_epr = df[df["source"] != "epraccur"]
        mask = ~non_epr["practice_code"].isin(reference_codes)
        return _make_result(
            "QR-08",
            "Practice code missing from EPRACCUR lookup",
            "error",
            non_epr,
            mask,
        )

    return rule_qr08_practice_in_epraccur


def make_qr09_non_active_practice_rule(status_by_code: dict[str, str | None]) -> RuleFn:
    def rule_qr09_non_active_practice(df: pd.DataFrame) -> RuleResult:
        non_epr = df[df["source"] != "epraccur"].copy()
        mapped_status = non_epr["practice_code"].map(status_by_code)
        mask = mapped_status.notna() & (mapped_status != "ACTIVE")
        return _make_result(
            "QR-09",
            "Non-EPRACCUR row references non-ACTIVE practice",
            "warning",
            non_epr,
            mask,
        )

    return rule_qr09_non_active_practice


def make_qr10_volume_drift_rule(
    baselines: dict[str, int] = SOURCE_BASELINES,
    tolerance: float = 0.15,
) -> RuleFn:
    def rule_qr10_source_volume(df: pd.DataFrame) -> RuleResult:
        drift_rows: list[dict] = []
        drifted_count = 0
        for src, expected in baselines.items():
            actual = int((df["source"] == src).sum())
            low = expected * (1.0 - tolerance)
            high = expected * (1.0 + tolerance)
            if not (low <= actual <= high):
                drifted_count += 1
                drift_rows.append(
                    {
                        "source": src,
                        "actual_rows": actual,
                        "expected_rows": expected,
                        "allowed_range": f"{int(low)}..{int(high)}",
                    }
                )
        return RuleResult(
            id="QR-10",
            name="Source volume outside +-15% baseline",
            severity="warning",
            passed=(drifted_count == 0),
            failed_count=drifted_count,
            total=len(baselines),
            samples=drift_rows[:5],
        )

    return rule_qr10_source_volume


def build_rules(df: pd.DataFrame) -> list[RuleFn]:
    epr = df[df["source"] == "epraccur"]
    ref_codes = set(epr["practice_code"].dropna().astype(str))
    status_by_code = dict(zip(epr["practice_code"], epr["status"]))

    return [
        rule_qr01_active_postcode,
        rule_qr02_epd_metrics_and_snomed,
        rule_qr03_epraccur_unique_code,
        rule_qr04_registrations_unique_code,
        rule_qr05_patient_count_range,
        rule_qr06_epd_quantity_and_cost_range,
        rule_qr07_uk_postcode_format,
        make_qr08_referential_rule(ref_codes),
        make_qr09_non_active_practice_rule(status_by_code),
        make_qr10_volume_drift_rule(),
    ]


def load_dataset(path: Path = LOADED_CSV_PATH, chunk_size: int = DEFAULT_CHUNK_SIZE) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Loaded dataset not found: {path}")

    # Read in chunks so large files keep memory predictable, then prepare types
    chunks: list[pd.DataFrame] = []
    for chunk in pd.read_csv(path, dtype=str, chunksize=chunk_size):
        chunks.append(prepare_df(chunk))

    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)


def run_quality_checks(df: pd.DataFrame) -> tuple[str, list[RuleResult]]:
    clean_df = prepare_df(df)
    rules = build_rules(clean_df)
    results = [rule_fn(clean_df) for rule_fn in rules]

    has_error_failure = any(
        (r.severity == "error") and (not r.passed) for r in results
    )
    overall_status = "FAIL" if has_error_failure else "PASS"
    return overall_status, results


def main(path: Path = LOADED_CSV_PATH) -> int:
    setup_logging()
    df = load_dataset(path)
    overall_status, results = run_quality_checks(df)

    for res in results:
        status_label = "PASS" if res.passed else "FAIL"
        logger.info(
            "%s [%s] (%s): %s | failed=%d / total=%d",
            res.id,
            res.severity.upper(),
            res.name,
            status_label,
            res.failed_count,
            res.total,
        )

    logger.info("Overall Quality Status: %s", overall_status)
    return 1 if overall_status == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
