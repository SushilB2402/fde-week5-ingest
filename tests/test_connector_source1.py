import pytest

from pydantic import ValidationError

from src.normalise import map_source1_row


def test_missing_practice_code():

    with pytest.raises(
        ValidationError
    ):

        map_source1_row(
            1,
            {
                "PRACTICE_CODE": None
            }
        )


def test_invalid_actual_cost():

    with pytest.raises(
        ValidationError
    ):

        map_source1_row(
            1,
            {
                "PRACTICE_CODE": "A81001",
                "ACTUAL_COST": "abc",
            }
        )

def test_good_row_maps_fields():

    rec = map_source1_row(
        2,
        {
            "PRACTICE_CODE": " a81001 ",
            "ACTUAL_COST": "10.5",
        },
    )

    assert (
        rec.practice_code
        == "A81001"
    )

    assert (
        rec.actual_cost
        == 10.5
    )
    