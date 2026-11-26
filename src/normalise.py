from src.schema import Record


def map_source1_row(
    source_row: int,
    row: dict,
) -> Record:

    return Record(

        source="epd",

        source_row=source_row,

        practice_code=row.get(
            "PRACTICE_CODE"
        ),

        practice_name=row.get(
            "PRACTICE_NAME"
        ),

        postcode=row.get(
            "POSTCODE"
        ),

        quantity=row.get(
            "QUANTITY"
        ),

        actual_cost=row.get(
            "ACTUAL_COST"
        ),

        snomed_code=row.get(
            "SNOMED_CODE"
        ),
    )

def normalise_text(
    value,
):

    if value is None:
        return None

    value = str(value).strip().upper()

    if value == "":
        return None

    return value

def map_source2_row(
    source_row: int,
    row: dict,
) -> Record:

    return Record(

        source="registrations",

        source_row=source_row,

        practice_code=normalise_text(
            row.get("CODE")
        ),

        postcode=normalise_text(
            row.get("POSTCODE")
        ),

        patient_count=row.get(
            "NUMBER_OF_PATIENTS"
        ),

        # Not present in source 2

        practice_name=None,
        status=None,
        quantity=None,
        actual_cost=None,
        snomed_code=None,
    )