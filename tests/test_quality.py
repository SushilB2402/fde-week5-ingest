import pandas as pd

from src.quality import (
    make_qr08_referential_rule,
    make_qr09_non_active_practice_rule,
    make_qr10_volume_drift_rule,
    rule_qr01_active_postcode,
    rule_qr03_epraccur_unique_code,
    rule_qr05_patient_count_range,
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
    assert res.failed_count == 2  # keep=False reports both copies


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
    assert res.failed_count == 2


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


def test_referential_rule_fails_orphan_practice_code():
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
    assert res.failed_count == 1


def test_consistency_and_volume_warning_rules_and_overall_status():
    df = pd.DataFrame(
        [
            {
                "source": "epraccur",
                "source_row": 1,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": "DORMANT",
                "patient_count": None,
                "quantity": None,
                "actual_cost": None,
                "snomed_code": None,
            },
            {
                "source": "epd",
                "source_row": 2,
                "practice_code": "A81001",
                "postcode": "TS18 1HU",
                "status": None,
                "patient_count": None,
                "quantity": "5",
                "actual_cost": "10.00",
                "snomed_code": "12345",
            },
        ]
    )

    qr09 = make_qr09_non_active_practice_rule({"A81001": "DORMANT"})(df)
    qr10 = make_qr10_volume_drift_rule({"epd": 1000}, tolerance=0.15)(df)
    assert qr09.passed is False and qr09.severity == "warning"
    assert qr10.passed is False and qr10.severity == "warning"

    overall_status, _ = run_quality_checks(df)
    assert overall_status == "FAIL"
    