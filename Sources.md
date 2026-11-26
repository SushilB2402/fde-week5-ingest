# Sources

## Project

Title: NHS GP Practice Data Integration and Quality Assessment

Objective:
Integrate prescribing, patient registration, and GP practice reference data using GP Practice Code as a common key. Identify data quality issues and perform referential integrity checks.

Downloaded By:
Sushil Bhosale

Download Date:
2026-11-23

---

## Source 1

Dataset:
English Prescribing Dataset (EPD) with SNOMED codes

Regional Scope:
REGIONAL_OFFICE_NAME = SOUTH EAST

File:
EPD_SNOMED_202609-000000000000.csv renamed to epd_snomed_202609.csv

Publisher:
NHS Business Services Authority (NHSBSA)

Download URL:
https://opendata.nhsbsa.net/dataset/english-prescribing-dataset-epd-with-snomed-code/resource/4d751d28-ace3-4692-938a-b930eff85822?filters=REGIONAL_OFFICE_NAME%3ASOUTH%2520EAST

Downloaded:
2026-11-23

Licence:
Open Government Licence 3.0 (United Kingdom)

Join Key:
PRACTICE_CODE

Rows Read:
63,839 (partial; 2,537,185 in the full filtered set)

Expected Use:
Prescription activity by prescribing organisation (mostly GP practices).

Profiling Findings:

- Dataset contains 63,839 prescribing records across 27 columns.
- No duplicate rows were identified.
- PRACTICE_CODE contains 1,028 unique practices and no missing values.
- POSTCODE contains 78 missing values.
- ADDRESS_2 contains 3,470 missing values and ADDRESS_4 contains 2,712 missing values.
- SNOMED_CODE contains 38 missing values.

Measured Defects:

- 78 records have a missing POSTCODE.
- 38 records have a missing SNOMED_CODE.
- 5 distinct PRACTICE_CODE values (20 rows, 0.03%) not found in EPRACCUR: 10Q998 (7), 8F7M3D (6), 91Q998 (5), 97R998 (1), NMS998 (1). None are Y-prefixed; all fail the standard letter-plus-five-digits format.
- 1 row has ACTUAL_COST = 0; no negative values.

Initial Observations:
- Large transactional dataset
- Contains multiple records per practice
- Includes prescribing costs and quantities
- Uses PRACTICE_CODE as identifier
- Includes SNOMED and BNF coding systems
- 2,477 Y-prefixed prescribing records
- Includes non-GP organisations (for example Y-prefixed codes such as hospitals and treatment services)

---

## Source 2

Dataset:
Patients Registered at a GP Practice

File:
gp-reg-pat-prac-all.csv

Publisher:
NHS England

Download URL:
https://digital.nhs.uk/data-and-information/publications/statistical/patients-registered-at-a-gp-practice/september-2026

Downloaded:
2026-11-23

Licence:
Open Government Licence 3.0 (United Kingdom)

Join Key:
CODE

Rows Read:
6128

Expected Use:
Patient population counts per GP practice.

Profiling Findings:

- Dataset contains 6,128 records across 10 columns.
- No duplicate rows were identified.
- CODE is unique across all 6,128 records.
- No missing values were identified in any column.
- NUMBER_OF_PATIENTS ranges from 1 to 120,539.
- All records share the same extract date: 2026-09-01.

Measured Defects:

- 16 practices have fewer than 100 registered patients (minimum 1).
- 7 registrations resolve to INACTIVE or DORMANT practices in EPRACCUR.
- [third: pending]

Measured Findings:

- 16 practices have fewer than 100 registered patients.
- 7 registration records reference INACTIVE or DORMANT practices in EPRACCUR.
- Patient counts range from 1 to 120,539, requiring validation against expected operational thresholds.

Quality Observation:
- Patient counts range from 1 to 120,539.

Initial Observations:
- One row per practice
- Contains patient counts
- Contains practice postcode
- Uses CODE rather than PRACTICE_CODE

---

## Source 3

Dataset:
EPRACCUR GP Practice Reference Data

File:
epraccur.csv

Publisher:
NHS Organisation Data Service (ODS)

Download URL:
https://digital.nhs.uk/services/organisation-data-service/data-search-and-export/csv-downloads/gp-and-gp-practice-related-data

Downloaded:
2026-11-23

Licence:
Open Government Licence 3.0 (United Kingdom)

Join Key:
Column 0 (Practice Code)

Rows Read:
15717

Expected Use:
Reference dataset for GP practices.

Profiling Findings:

- Dataset contains 15,717 records across 27 columns.
- No duplicate rows were identified.
- Practice code column contains 15,717 unique values.
- Several columns contain a high proportion of null values.
- Column 5 contains 4,533 null values.
- Column 6 contains 12,796 null values.
- Column 17 contains 361 null values.


Measured Defects:

- 3,096 records (19.7%) are not active: 2,843 INACTIVE and 253 DORMANT.
- [second: pending]
- [third: pending]

Initial Observations:
- No header row
- Contains practice status information
- Contains address information
- Contains postcode
- Requires explicit schema definition

---

# Planned Integration

Common Business Key:

GP Practice Code

Source 1:
PRACTICE_CODE

Source 2:
CODE

Source 3:
Column 0

Standardised Name:
PRACTICE_CODE

---

## Known Limitations

The three datasets are not perfectly aligned in time.

- Source 1 contains September 2026 prescribing activity.
- Source 2 contains September 2026 patient registration data.
- Source 3 is a reference dataset downloaded on 2026-11-23.

Source 1 is a partial extract: 63,839 of 2,537,185 records for the
SOUTH EAST filter (about 2.5%), checked against the portal on 2026-11-24.
The file used is ...000000000000.csv. The cause of the partial count has not been confirmed. Prescribing volumes and costs must not be interpreted. The extract is used to test integration and data quality logic only.

Practices that opened, closed, merged, or changed status between these dates may appear in one source but not another.

Primary referential integrity check:

EPD PRACTICE_CODE -> EPRACCUR Practice Code

The reverse check may produce expected exceptions due to differing scope and snapshot dates.

---

## Success Metrics

### Pipeline Metrics

- At least 50,000 rows processed across all sources.
- One command executes the complete pipeline.
- Every rejected row has a documented rejection reason.
- 8-10 automated data quality rules are implemented.
- Reconciliation holds for every source:
  source rows = loaded rows + rejected rows.
- Another engineer can reproduce the project using the README.

### Data Quality Metrics

- At least three measurable quality issues identified per source.
- GP Practice Codes standardised across all datasets.
- Referential integrity checks executed against EPRACCUR.
- Quality check results exported and reproducible.
- Source-to-target row counts documented.