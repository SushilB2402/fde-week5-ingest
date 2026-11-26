import pytest

from pydantic import ValidationError

from src.normalise import map_source2_row


def test_negative_patient_count():

    with pytest.raises(
        ValidationError
    ):

        map_source2_row(
            1,
            {
                "CODE": "A81001",
                "NUMBER_OF_PATIENTS": "-5",
            },
        )


def test_blank_code():

    with pytest.raises(
        ValidationError
    ):

        map_source2_row(
            1,
            {
                "CODE": None,
            },
        )


def test_good_row_maps_fields():

    rec = map_source2_row(
        2,
        {
            "CODE": " a81001 ",
            "POSTCODE": "TS18 1HU",
            "NUMBER_OF_PATIENTS": "12345",
        },
    )

    assert rec.practice_code == "A81001"
    assert rec.patient_count == 12345
    assert rec.postcode == "TS18 1HU"
