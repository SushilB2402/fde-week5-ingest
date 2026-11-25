from pathlib import Path
import pandas as pd

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

RAW_DIR = Path("data/raw")

SOURCES = [
    {
        "name": "EPD Prescribing",
        "file": RAW_DIR / "epd_snomed_202609.csv",
        "code_column": "PRACTICE_CODE",
    },
    {
        "name": "GP Registrations",
        "file": RAW_DIR / "gp-reg-pat-prac-all.csv",
        "code_column": "CODE",
    },
    {
        "name": "EPRACCUR",
        "file": RAW_DIR / "epraccur.csv",
        "code_column": 0,
        "header": None,
    },
]


# -----------------------------------------------------------------------------
# PROFILING FUNCTION
# -----------------------------------------------------------------------------

def profile_dataset(source):

    print("\n" + "=" * 100)
    print(f"DATASET: {source['name']}")
    print("=" * 100)

    kwargs = {"low_memory": False}

    if "header" in source:
        kwargs["header"] = source["header"]

    df = pd.read_csv(
        source["file"],
        **kwargs
    )

    print("\nColumns:")
    print(df.columns.tolist())

    print("\n1. SHAPE")
    print(df.shape)

    print("\n2. DATA TYPES")
    print(df.dtypes)

    print("\n3. NULL VALUES")
    print(df.isna().sum())

    print("\n4. DUPLICATE ROWS")
    print(df.duplicated().sum())

    print("\n5. DESCRIBE")
    print(df.describe(include="all"))

    key_col = source["code_column"]

    print("\n6. KEY COLUMN")
    print(f"Column: {key_col}")

    print("\nUnique Values:")
    print(df[key_col].nunique())

    print("\nMissing Keys:")
    print(df[key_col].isna().sum())

    print("\nIs Unique:")
    print(df[key_col].is_unique)

    print("\nTop 20 Values:")
    print(df[key_col].value_counts().head(20))

    postcode_candidates = [
        "POSTCODE",
        "Postcode",
        9,
    ]

    for col in postcode_candidates:
        if col in df.columns:

            print("\n7. POSTCODE ANALYSIS")
            print(f"Column: {col}")

            print("\nMissing Postcodes:")
            print(df[col].isna().sum())

            print("\nTop 20 Postcodes:")
            print(df[col].value_counts().head(20))

            break

    print("\nEND OF DATASET")


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------

if __name__ == "__main__":

    for source in SOURCES:
        profile_dataset(source)
        