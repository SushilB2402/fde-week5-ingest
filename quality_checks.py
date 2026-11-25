from pathlib import Path
import pandas as pd

# ------------------------------------------------------------------
# LOAD DATA
# ------------------------------------------------------------------

RAW_DIR = Path("data/raw")

epd = pd.read_csv(
    RAW_DIR / "epd_snomed_202609.csv",
    low_memory=False
)

reg = pd.read_csv(
    RAW_DIR / "gp-reg-pat-prac-all.csv",
    low_memory=False
)

epraccur = pd.read_csv(
    RAW_DIR / "epraccur.csv",
    header=None,
    low_memory=False
)

# ------------------------------------------------------------------
# SOURCE 1 - EPD QUALITY CHECKS
# ------------------------------------------------------------------

missing_codes = set(epd["PRACTICE_CODE"]) - set(epraccur[0])

print("\nEPD codes missing from EPRACCUR:")
print(len(missing_codes))

y_prefix = epd["PRACTICE_CODE"].astype(str).str.startswith("Y").sum()

print("\nY-prefix prescribing records:")
print(y_prefix)

zero_or_negative_cost = (epd["ACTUAL_COST"] <= 0).sum()

print("\nACTUAL_COST <= 0:")
print(zero_or_negative_cost)

zero_or_negative_quantity = (epd["QUANTITY"] <= 0).sum()

print("\nQUANTITY <= 0:")
print(zero_or_negative_quantity)

# ------------------------------------------------------------------
# SOURCE 2 - GP REGISTRATION CHECKS
# ------------------------------------------------------------------

missing_reg_codes = (
    set(reg["CODE"])
    - set(epraccur[0])
)

print("\nRegistration codes missing from EPRACCUR:")
print(len(missing_reg_codes))

small_lists = (
    reg["NUMBER_OF_PATIENTS"] < 100
).sum()

print("\nPractices with fewer than 100 patients:")
print(small_lists)

# ------------------------------------------------------------------
# CHECK A
# Source 2 codes linked to inactive/dormant EPRACCUR records
# ------------------------------------------------------------------

inactive_statuses = {"INACTIVE", "DORMANT"}

inactive_practices = set(
    epraccur[
        epraccur[12].isin(inactive_statuses)
    ][0]
)

reg_inactive = (
    reg["CODE"]
    .isin(inactive_practices)
    .sum()
)

print("\nSource 2 codes linked to INACTIVE/DORMANT EPRACCUR records:")
print(reg_inactive)

# ------------------------------------------------------------------
# SOURCE 3 - EPRACCUR CHECKS
# ------------------------------------------------------------------

print("\nEPRACCUR Status Counts:")
print(
    epraccur[12]
    .value_counts(dropna=False)
)

# ------------------------------------------------------------------
# CHECK B
# Missing postcode count in EPRACCUR
# ------------------------------------------------------------------

missing_postcodes = (
    epraccur[9]
    .isna()
    .sum()
)

print("\nEPRACCUR missing postcodes:")
print(missing_postcodes)

# ------------------------------------------------------------------
# OPTIONAL SUMMARY
# ------------------------------------------------------------------

print("\n" + "=" * 60)
print("QUALITY CHECKS COMPLETE")
print("=" * 60)
