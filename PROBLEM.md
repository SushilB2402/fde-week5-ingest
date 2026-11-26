# NHS GP Practice Data Integration and Quality Assessment Pipeline

## Problem Statement

A fictional NHS analytics team wants to combine prescribing activity, patient registration counts and GP practice reference data to support reliable operational reporting.

Although these datasets describe the same organisations, they are published independently, use different schemas and naming conventions, and contain data quality issues that prevent straightforward integration.

The objective of this project is to build a reproducible Python-based ingestion and validation pipeline that loads multiple NHS datasets, standardises business keys, performs quality checks, validates referential integrity and produces reconciliation and quality reports.

---

## Business Context

Healthcare datasets are commonly published separately for operational and reporting purposes.

Analysts wishing to compare prescribing activity against registered patient populations or organisational status must first integrate multiple datasets into a consistent format.

Without standardisation and validation, reporting can be affected by:

- Missing identifiers
- Missing reference data
- Inactive organisations
- Schema inconsistencies
- Referential integrity failures

This project simulates a realistic data engineering workflow involving ingestion, normalisation, validation, reconciliation and reporting.

---

## Source Systems

### Source 1 – English Prescribing Dataset (EPD)

A transactional prescribing dataset containing prescription items, quantities, costs and SNOMED mappings for prescribing organisations (mostly GP practices).

Characteristics:

- Uses `PRACTICE_CODE`
- Multiple records per organisation
- Includes prescription quantities and costs
- Contains GP and non-GP organisations
- South East regional extract
- Partial extract: 63,839 of 2,537,185 source records

Observed quality issues:

- Missing postcode values
- Missing SNOMED codes
- Practice codes not found in reference data

---

### Source 2 – GP Practice Patient Registrations

A monthly snapshot containing registered patient counts by GP practice.

Characteristics:

- Uses `CODE`
- One row per practice
- Monthly population snapshot

Observed quality issues:

- Extremely small patient lists
- Registrations linked to inactive organisations

---

### Source 3 – EPRACCUR GP Practice Reference Data

Reference dataset containing organisation details, location information and operational status.

Characteristics:

- No header row
- Uses practice code as the primary identifier
- Contains ACTIVE, INACTIVE and DORMANT organisations
- Used as the reference source for validation

Design decision:

All records will be loaded. Operational status will be retained and reported rather than filtering inactive organisations during ingestion. This allows inactive practices to be distinguished from genuinely unknown codes.

---

## Integration Challenges

The datasets cannot be joined directly because they contain structural and quality differences:

- Different key names (`PRACTICE_CODE`, `CODE`, unnamed column)
- Different dataset granularity
- Different publication dates
- Missing values
- Headerless source file
- Active and inactive organisations
- Referential integrity failures

These differences create a realistic data engineering problem requiring standardisation and validation before analysis can be performed.

---

## Proposed Solution

Build a Python-based ingestion pipeline that:

1. Loads all source files.
2. Applies schema standardisation.
3. Standardises GP Practice Codes.
4. Performs quality validation.
5. Executes referential integrity checks against EPRACCUR.
6. Produces reconciliation statistics.
7. Generates quality reports.
8. Exports validated outputs.

The pipeline will be deterministic, repeatable and executable from a single command.

---

## Outputs

`data/out/loaded_*.csv`

Validated records per source in the common schema.

`data/out/rejected.jsonl`

Every rejected record including:

- source
- row number
- raw record
- rejection reason

`reports/run_<timestamp>.md`

Data quality report containing:

- rows read
- rows loaded
- rows rejected
- rule outcomes
- rejection reasons
- reconciliation results

---

## Out of Scope

- No database implementation
- No dashboard or visualisation layer
- No workflow scheduling
- No incremental loads
- No API ingestion
- File-based ingestion only
- No analysis of prescribing volumes or costs
- No correction of bad source data

Records failing validation will be rejected and logged rather than modified.

---

## Data Quality Objectives

The pipeline will assess:

- Missing mandatory fields
- Missing postcodes
- Missing SNOMED codes
- Duplicate records
- Invalid practice codes
- Referential integrity failures
- Inactive organisations
- Cost anomalies
- Quantity anomalies

---

## Success Metrics

- [ ] At least 50,000 rows read across all sources (currently 85,684).
- [ ] One command (`make run`) executes the entire pipeline.
- [ ] Every rejected record is written to `rejected.jsonl` with a reason.
- [ ] 8–10 quality rules execute and appear in the report.
- [ ] Referential checks report found-active, found-inactive and not-found counts.
- [ ] For every source: source rows = loaded rows + rejected rows.
- [ ] Quality and reconciliation reports are generated successfully.
- [ ] A second person can run the project from the README alone by Sunday 29 Nov 2026.

---

## Known Limitations

Prescribing data represents September 2026, South East only, and is a partial extract (63,839 of 2,537,185 records, approximately 2.5% of the source dataset). Prescribing volumes and costs must not be interpreted as representative of wider activity.

Patient registrations are recorded as at 1 September 2026.

EPRACCUR was downloaded on 23 November 2026 and includes ACTIVE, INACTIVE and DORMANT organisations.

Source 1 includes non-GP organisations represented by Y-prefixed organisation codes.

The source datasets do not represent identical snapshots in time and may therefore contain expected differences in organisational status.