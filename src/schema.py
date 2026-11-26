from typing import Literal
from typing import Optional

from pydantic import BaseModel
from pydantic import field_validator


class Record(BaseModel):
    """
    Common schema used by all source systems.

    All source-specific records must be mapped into this model.

    Design decision:
    Load and standardise data here.
    Flag business-rule violations later in quality.py.
    """

    # ------------------------------------------------------------------
    # Traceability
    # ------------------------------------------------------------------

    source: str
    source_row: int

    # ------------------------------------------------------------------
    # Common business key
    # ------------------------------------------------------------------

    practice_code: str

    # ------------------------------------------------------------------
    # Common attributes
    # ------------------------------------------------------------------

    practice_name: Optional[str] = None

    postcode: Optional[str] = None

    status: Optional[
        Literal[
            "ACTIVE",
            "INACTIVE",
            "DORMANT",
        ]
    ] = None

    # ------------------------------------------------------------------
    # Source 2 fields
    # ------------------------------------------------------------------

    patient_count: Optional[int] = None

    # ------------------------------------------------------------------
    # Source 1 fields
    # ------------------------------------------------------------------

    quantity: Optional[float] = None

    actual_cost: Optional[float] = None

    snomed_code: Optional[str] = None

    # ------------------------------------------------------------------
    # Validators
    # ------------------------------------------------------------------

    @field_validator("practice_code")
    @classmethod
    def validate_practice_code(
        cls,
        value: str,
    ) -> str:
        """
        Standardise practice codes.

        Do NOT enforce business patterns here.
        Unusual codes are flagged later by quality rules.
        """

        value = value.strip().upper()

        if not value:
            raise ValueError(
                "practice_code cannot be empty"
            )

        return value

    @field_validator("patient_count")
    @classmethod
    def validate_patient_count(
        cls,
        value,
    ):
        """
        Negative patient counts are impossible.
        """

        if value is None:
            return value

        if value < 0:
            raise ValueError(
                "patient_count cannot be negative"
            )

        return value

    @field_validator("quantity")
    @classmethod
    def validate_quantity(
        cls,
        value,
    ):
        """
        Negative quantities are not valid.
        Zero is allowed and can be reviewed later.
        """

        if value is None:
            return value

        if value < 0:
            raise ValueError(
                "quantity cannot be negative"
            )

        return value

    @field_validator("source")
    @classmethod
    def validate_source(
        cls,
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "source cannot be empty"
            )

        return value

    @field_validator("source_row")
    @classmethod
    def validate_source_row(
        cls,
        value: int,
    ) -> int:

        if value < 1:
            raise ValueError(
                "source_row must be greater than zero"
            )

        return value
    