import pytest
from pydantic import ValidationError

from src.normalise import normalise_text
from src.schema import Record


def test_valid_record_and_normalisation():
    assert normalise_text("  ts18 1hu ") == "TS18 1HU"
    assert normalise_text("   ") is None
    assert normalise_text(None) is None

    rec = Record(
        source="epraccur",
        source_row=1,
        practice_code=normalise_text(" a81001 "),
        practice_name="THE DENSHAM SURGERY",
        postcode=normalise_text(" ts18 1hu "),
        status="ACTIVE",
        patient_count=0,
        quantity=0.0,
        actual_cost=12.50,
        snomed_code="123456789",
    )

    assert rec.practice_code == "A81001"
    assert rec.postcode == "TS18 1HU"
    assert rec.status == "ACTIVE"
    assert rec.patient_count == 0
    assert rec.quantity == 0.0


def test_blank_practice_code_rejected():
    with pytest.raises(ValidationError):
        Record(
            source="registrations",
            source_row=1,
            practice_code=normalise_text("   "),
            patient_count=100,
        )


def test_negative_count_rejected():
    with pytest.raises(ValidationError):
        Record(
            source="registrations",
            source_row=2,
            practice_code="A81001",
            patient_count=-1,
        )


def test_negative_quantity_rejected():
    with pytest.raises(ValidationError):
        Record(
            source="epd",
            source_row=3,
            practice_code="A81001",
            quantity=-0.5,
        )


def test_invalid_status_rejected():
    with pytest.raises(ValidationError):
        Record(
            source="epraccur",
            source_row=4,
            practice_code="A81001",
            status="PROPOSED",
        )


def test_source_row_must_be_positive():
    with pytest.raises(ValidationError):
        Record(
            source="epd",
            source_row=0,
            practice_code="A81001",
        )
        