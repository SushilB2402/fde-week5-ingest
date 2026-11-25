# NHS GP Practice Data Integration and Quality Assessment Pipeline

## Problem Statement

NHS prescribing, patient registration and GP practice reference data are published independently by different organisations and in different formats. Although all three datasets describe GP practices, they cannot be joined directly because they use different schemas, naming conventions and levels of data quality.

The objective of this project is to build a reproducible data ingestion and quality assessment pipeline that integrates multiple NHS datasets using GP Practice Code as a shared business key. The pipeline will standardise schemas, validate records, perform referential integrity checks and generate quality reports suitable for downstream analysis.

---

## Business Context

Healthcare datasets are frequently published separately for operational and reporting purposes. Analysts wishing to understand prescribing behaviour relative to patient population or organisational status must first integrate the data into a consistent and reliable format.

Without standardisation and validation, reporting may be affected by:

- Missing identifiers
- Inconsistent schema definitions
- Inactive organisations
- Missing reference data
- Referential integrity failures

The project simulates a real-world data engineering workflow involving ingestion, normalisation, validation, reconciliation and reporting.

---

## Source Systems

### Source 1 – English Prescribing Dataset (EPD)

The English Prescribing Dataset contains prescribing activity for GP practices, including prescription volume, quantity, cost and SNOMED mappings.

Characteristics:

- Transactional dataset
- Uses `PRACTICE_CODE`
- Multiple rows per practice
- Includes prescribing costs and quantities
- South East regional extract

Observed quality issues:

- Missing postcode values
- Missing SNOMED codes
- Practice codes not present in reference data

---

### Source 2 – GP Practice Patient Registrations

This dataset provides monthly counts of registered patients per GP practice.

Characteristics:

- One row per practice
- Uses `CODE`
- Includes registered patient totals
- Monthly snapshot data

Observed quality issues:

- Extremely small practice populations
- References to practices that are not currently active

---

### Source 3 – EPRACCUR GP Practice Reference Data

EPRACCUR provides organisational reference information for GP practices.

Characteristics:

- Reference dataset
- No header row
- Contains organisation status information
- Used as the authoritative reference source for validation

Observed quality issues:

- INACTIVE organisations
- DORMANT organisations
- Mixed operational statuses requiring filtering before validation

---

## Integration Challenges

The datasets are intentionally difficult to integrate because they contain structural and quality differences.

Key challenges include:

- Different key names (`PRACTICE_CODE`, `CODE`, and unnamed reference columns)
- Different levels of granularity
- Different snapshot dates
- Missing values
- Inactive organisations within reference data
- Headerless source files
- Referential integrity failures

These issues create a realistic data engineering problem that requires standardisation and quality controls before analysis can take place.

---

## Proposed Solution

Build a Python-based ingestion pipeline that:

1. Loads each source dataset.
2. Applies schema standardisation.
3. Standardises GP Practice Codes.
4. Executes automated quality checks.
5. Validates records against EPRACCUR.
6. Produces reconciliation outputs.
7. Generates data quality reports.
8. Exports validated datasets for analysis.

The pipeline should be repeatable, testable and executable from a single command.

---

## Data Quality Objectives

The pipeline will assess:

- Missing mandatory fields
- Duplicate records
- Invalid GP Practice Codes
- Invalid organisational status
- Missing reference records
- Missing postcodes
- Missing SNOMED codes
- Cost and quantity anomalies
- Referential integrity violations

---

## Success Metrics

The project will be considered successful if:

- All datasets are loaded successfully.
- GP Practice Codes are standardised across all sources.
- Automated quality checks execute consistently.
- Every source satisfies reconciliation requirements.
- Source rows equal loaded rows plus rejected rows.
- Rejected rows are logged with a rejection reason.
- Referential integrity checks are performed against EPRACCUR.
- Quality and reconciliation reports are generated.
- Another engineer can reproduce the pipeline using the project documentation.

---

## Known Limitations

The datasets do not represent identical snapshots in time.

- Prescribing data represents 
