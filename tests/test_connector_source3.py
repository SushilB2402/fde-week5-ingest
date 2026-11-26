import pytest
from pydantic import ValidationError
from src.normalise import map_source3_row


def test_invalid_status():
    with pytest.raises(ValidationError):
        map_source3_row(
            1,
            {
                "PRACTICE_CODE": "A81001",
                "POSTCODE": "TS18 1PW",
                "STATUS": "OPEN",
            },
        )


def test_blank_code():
    with pytest.raises(ValidationError):
        map_source3_row(
            1,
            {
                "PRACTICE_CODE": "   ",
                "POSTCODE": "TS18 1PW",
                "STATUS": "ACTIVE",
            },
        )


def test_good_row():
    rec = map_source3_row(
        1,
        {
            "PRACTICE_CODE": " a81001 ",
            "POSTCODE": " ts18 1pw ",
            "STATUS": "ACTIVE",
        },
    )

    assert rec.practice_code == "A81001"
    assert rec.postcode == "TS18 1PW"
    assert rec.status == "ACTIVE"
    