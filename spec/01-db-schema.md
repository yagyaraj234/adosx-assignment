# DB Schema — Spec

Part of [00-index.md](./00-index.md). Depends on: nothing. Depended on by: 02, 04.

## Problem Statement

Three dirty CSVs (System A records, System B entries, locations) need a durable, queryable
store before any comparison or API work can happen.

## Solution

Three tables mirroring the three CSVs 1:1, with no derived/normalized state — normalization
(ref matching, org resolution) happens in code (specs 03/04), not in the schema.

## User Stories

1. As the importer, I want one table per CSV with columns matching the CSV's fields, so that
   no import-time transformation is needed beyond type coercion.
2. As the importer, I want numeric fields stored as both their raw string and a nullable
   parsed number, so that dirty values are preserved for display without blocking storage.
3. As an engineer, I want the schema recreated fresh on every process start from the CSVs,
   so that there's no migration state to keep in sync with a fixed, static submission
   dataset.

## Implementation Decisions

- **`SystemARecord`**: one row per `system_a.csv` row — `record_id` (str, primary key),
  `location_id` (str), `total_value_raw` (str), `total_value` (float, nullable).
- **`SystemBEntry`**: one row per `system_b.csv` row — `entry_id` (str, primary key),
  `record_ref_raw` (str, unnormalized — normalization is spec 03's job, not stored),
  `location_id` (str), `value_raw` (str), `value` (float, nullable).
- **`Location`**: one row per `locations.csv` row — `location_id` (str, primary key),
  `org_id` (str), `location_name` (str).
- **SQLModel + SQLite**, not Postgres — brief states performance/infra aren't graded;
  SQLite needs zero setup and survives a clean clone.
- **No Alembic / migrations tooling** — schema is fixed for this submission; DB is
  dropped and recreated from the CSVs on every app startup (see spec 02).
- Every other field the CSVs carry (dates, category codes, actor IDs, labels) is stored
  as-is for completeness but is not read by the comparison engine (spec 03) or the API
  (spec 04) — kept only so the importer doesn't have to special-case which columns matter.

## Testing Decisions

Not TDD in the red-green sense — a schema has no behavior to drive with a failing test.
Verified implicitly by every spec 02/04 test: if a column were missing or mistyped, the
importer or API tests would fail on a `KeyError`/type error.

## Out of Scope

- Indexes/performance tuning — 120 rows per file, not graded.
- Foreign key constraints between tables — the whole point of the exercise is that
  `record_ref`/`location_id` references are dirty and don't always resolve; a hard FK
  would make the importer reject rows it's required to keep (see spec 02).

## Further Notes

None.
