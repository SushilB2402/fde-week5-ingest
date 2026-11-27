import pandas as pd

from src.quality import (
    make_qr08_referential_rule,
    make_qr09_non_active_practice_rule,
    make_qr10_volume_drift_rule,
    rule_qr01_active_postcode,
    rule_qr02_epd_metrics_and_snomed,
    rule_qr03_epraccur_unique_code,
    rule_qr04_registrations_unique_code,
    rule_qr05_patient_count_range,
    rule_qr06_epd_quantity_and_cost_range,
    rule_qr07_uk_postcode_format,
    run_quality_checks,
)


def test_null_rule_fails_active_practice_missing_postcode():
    df = pd.DataFrame(
        [
            {
                "source": "epraccur",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "   ",
                "status": "ACTIVE",
            }
        ]
    )

    res = rule_qr01_active_postcode(df)
    assert res.passed is False
    assert res.failed_count == 1
    assert len(res.samples) <= 5


def test_qr02_fails_when_epd_metric_missing():
    df = pd.DataFrame(
        [
            {
                "source": "epd",
                "source_row": 1,
                "practice_code": "A81001",
                "quantity": None,
                "actual_cost": "10.00",
                "snomed_code": "12345",
            }
        ]
    )

    res = rule_qr02_epd_metrics_and_snomed(df)
    assert res.passed is False
    assert res.severity == "error"
    assert res.failed_count == 1

def test_qr02_warns_when_snomed_null_rate_exceeds_1_percent():
    rows = [
        {
            "source": "epd",
            "source_row": idx + 1,
            "practice_code": "A81001",
            "quantity": "10",
            "actual_cost": "5.00",
            "snomed_code": None if idx < 5 else "123456",
        }
        for idx in range(10)
    ]
    df = pd.DataFrame(rows)

    res = rule_qr02_epd_metrics_and_snomed(df)
    assert res.passed is False
    assert res.severity == "warning"
    assert res.failed_count == 5


def test_main_exit_code_reflects_error_vs_warning(tmp_path):
    from src.quality import main

    warning_only_csv = tmp_path / "warn_only.csv"
    pd.DataFrame(
        [
            {
                "source": "epraccur",
                "source_row": "1",
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": "ACTIVE",
                "patient_count": "",
                "quantity": "",
                "actual_cost": "",
                "snomed_code": "",
            },
            {
                "source": "registrations",
                "source_row": "1",
                "practice_code": "E84066",
                "postcode": "HA9 6PW",
                "status": "",
                "patient_count": "120539",
                "quantity": "",
                "actual_cost": "",
                "snomed_code": "",
            },
        ]
    ).to_csv(warning_only_csv, index=False)

    assert main(warning_only_csv) == 0

    error_csv = tmp_path / "error.csv"
    pd.DataFrame(
        [
            {
                "source": "epraccur",
                "source_row": "1",
                "practice_code": "A81001",
                "postcode": "   ",
                "status": "ACTIVE",
                "patient_count": "",
                "quantity": "",
                "actual_cost": "",
                "snomed_code": "",
            }
        ]
    ).to_csv(error_csv, index=False)

    assert main(error_csv) == 1

def test_duplicate_rule_fails_duplicate_epraccur_code():
    df = pd.DataFrame(
        [
            {
                "source": "epraccur",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": "ACTIVE",
            },
            {
                "source": "epraccur",
                "source_row": 2,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": "ACTIVE",
            },
        ]
    )

    res = rule_qr03_epraccur_unique_code(df)
    assert res.passed is False
    assert res.failed_count == 2


def test_qr04_fails_duplicate_registrations_code():
    df = pd.DataFrame(
        [
            {
                "source": "registrations",
                "source_row": 1,
                "practice_code": "A81001",
                "patient_count": "1200",
            },
            {
                "source": "registrations",
                "source_row": 2,
                "practice_code": "A81001",
                "patient_count": "1300",
            },
        ]
    )

    res = rule_qr04_registrations_unique_code(df)
    assert res.passed is False
    assert res.failed_count == 2


def test_range_rule_fails_out_of_bounds_patient_count():
    df = pd.DataFrame(
        [
            {
                "source": "registrations",
                "source_row": 1,
                "practice_code": "A81001",
                "patient_count": "0",
            },
            {
                "source": "registrations",
                "source_row": 2,
                "practice_code": "A81002",
                "patient_count": "250000",
            },
        ]
    )

    res = rule_qr05_patient_count_range(df)
    assert res.passed is False
    assert res.severity == "error"
    assert res.failed_count == 1


def test_qr06_flags_zero_cost_as_warning():
    df = pd.DataFrame(
        [
            {
                "source": "epd",
                "source_row": 1,
                "practice_code": "A81001",
                "quantity": "10",
                "actual_cost": "0.00",
            }
        ]
    )

    res = rule_qr06_epd_quantity_and_cost_range(df)
    assert res.passed is False
    assert res.severity == "warning"
    assert res.failed_count == 1


def test_format_rule_fails_malformed_postcode():
    df = pd.DataFrame(
        [
            {
                "source": "epd",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "NOT A POSTCODE",
            }
        ]
    )

    res = rule_qr07_uk_postcode_format(df)
    assert res.passed is False
    assert res.failed_count == 1


def test_referential_rule_flags_orphan_practice_code():
    df = pd.DataFrame(
        [
            {
                "source": "epd",
                "source_row": 1,
                "practice_code": "Z99999",
                "postcode": "TS18 1HU",
            }
        ]
    )

    rule_fn = make_qr08_referential_rule({"A81001"})
    res = rule_fn(df)
    assert res.passed is False
    assert res.severity == "warning"
    assert res.failed_count == 1


def test_consistency_rule_flags_non_active_practice():
    df = pd.DataFrame(
        [
            {
                "source": "epd",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
            }
        ]
    )

    res = make_qr09_non_active_practice_rule({"A81001": "DORMANT"})(df)
    assert res.passed is False
    assert res.severity == "warning"
    assert res.failed_count == 1


def test_volume_rule_flags_source_drift():
    df = pd.DataFrame(
        [
            {
                "source": "epd",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
            }
        ]
    )

    res = make_qr10_volume_drift_rule({"epd": 1000}, tolerance=0.15)(df)
    assert res.passed is False
    assert res.severity == "warning"
    assert res.failed_count == 1


def test_clean_dataset_passes_with_status_pass():
    df = pd.DataFrame(
        [
            {
                "source": "epraccur",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": "ACTIVE",
                "patient_count": None,
                "quantity": None,
                "actual_cost": None,
                "snomed_code": None,
            },
            {
                "source": "registrations",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": None,
                "patient_count": "1500",
                "quantity": None,
                "actual_cost": None,
                "snomed_code": None,
            },
            {
                "source": "epd",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": None,
                "patient_count": None,
                "quantity": "20",
                "actual_cost": "12.50",
                "snomed_code": "999999",
            },
        ]
    )

    overall_status, results = run_quality_checks(df)
    assert overall_status == "PASS"
    assert all(r.passed for r in results if r.id != "QR-10")
    