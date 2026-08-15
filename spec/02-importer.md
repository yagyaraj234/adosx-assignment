# Importer — Spec

Part of [00-index.md](./00-index.md). Depends on: 01. Depended on by: 04.

## Problem Statement

The three CSVs are deliberately dirty — blank fields, unparseable numbers, `record_ref`
written three different ways, an entry pointing at a record that doesn't exist. The
importer must load all of it into the schema from spec 01 without ever silently dropping a
row, since a dropped row is a disagreement nobody will ever see.

## Solution

A row-by-row import (`backend/app/importer.py`, `backend/app/parsing.py`) that stores every
row regardless of whether its fields parse, falling back to `None`/raw-string preservation
instead of raising or skipping.

## User Stories

1. As an operator, I want every row of `system_a.csv` and `system_b.csv` imported even when
   a numeric field is blank or not a parseable number, so that no event is silently missing
   from the disagreement check.
2. As an operator, I want a numeric field that fails to parse stored as `None` (with its raw
   string kept for display), so that it later surfaces as a `value_mismatch` in spec 03
   instead of vanishing.
3. As an operator, I want the DB reset and re-imported fresh on every app start, so that
   there's no stale state between runs of this static dataset.
4. As an engineer, I want a test proving row-count-in equals row-count-out on a synthetic
   dirty CSV, so that a future change can't reintroduce silent row-dropping without a test
   catching it.

## Implementation Decisions

- **Parsing is lenient, storage never rejects.** `parse_number` (`backend/app/parsing.py`)
  returns `None` on anything it can't parse (blank, non-numeric, malformed) rather than
  raising; the importer stores the raw string regardless of parse success.
- **`record_ref` is imported raw, unnormalized.** Normalization (`normalize_ref`) is a
  read-time concern used by the comparison engine (spec 03), not an import-time
  transformation — keeps the DB a faithful copy of the source file.
- **Reset-and-reimport, not incremental/upsert.** `reset_db()` drops and recreates all
  tables before `import_data()` runs, every process start (see spec 01, Implementation
  Decisions).
- **No row is ever skipped**, including: blank value, unparseable value, a `record_ref`
  that doesn't match any System A record (that's a real disagreement, not an import error —
  see spec 03), and a `location_id` not present in `locations.csv` (see spec 04's
  `UNRESOLVED` bucket).

## Testing Decisions

- `backend/tests/test_importer.py`: import a synthetic dirty CSV (blank value, unparseable
  value, dangling ref, un-prefixed ref) and assert row-count-in == row-count-out — this is
  the one test that directly proves the "never silently drop a row" requirement.
- TDD order for this seam: write the row-count assertion against a dirty fixture first (red
  — fails against any importer that filters or raises), then implement the lenient
  parse-and-store path (green).
- Prior art: same assertion style as spec 03's tests — assert on the shape of the output
  collection, not on internal parsing steps.

## Out of Scope

- Schema/format validation beyond "does it parse as a number" — e.g. no date-format
  validation, no category-code whitelist. Not required by the brief and not exercised by
  the comparison engine.
- Incremental import / change detection — dataset is static for this submission.

## Further Notes

None.
