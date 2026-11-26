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
