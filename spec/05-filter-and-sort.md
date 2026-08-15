# Filter and Sort — Spec

Part of [00-index.md](./00-index.md). Depends on: 04. Depended on by: 06.

## Problem Statement

A reviewer scanning dozens of disagreements needs to narrow to one reason at a time and
find the largest discrepancies first — without building a general query/search feature the
brief doesn't ask for ("filter by reason, sort by value. That is enough.").

## Solution

Two optional query params on `GET /api/disagreements`: `reason` (exact match filter) and
`sort` (`value` or `-value`).

## User Stories

1. As a reviewer, I want to filter the disagreements list to one reason
   (`missing_in_b`/`orphan_ref`/`duplicate_in_b`/`value_mismatch`), so that I can work
   through one category at a time instead of scanning a mixed list.
2. As a reviewer, I want to sort the list by value ascending or descending, so that I can
   find the largest discrepancies first.
3. As a reviewer, I want a disagreement missing one side's value (e.g. `missing_in_b`, which
   has no System B value) to still sort sensibly rather than crash or vanish, so that
   incomplete rows don't break the sort.

## Implementation Decisions

- **`reason` param**: exact-match filter against the `reason` field applied *after*
  `find_disagreements` (spec 03) runs and *after* org-scoping (spec 04) — filtering never
  changes which disagreements exist, only which are returned.
- **`sort` param**: `value` (ascending, default) or `-value` (descending), validated by
  pattern (`^-?value$`) — an invalid value is a 422 from FastAPI's own query validation, not
  a silent no-op.
- **Sort key resolution**: each row's `sort_value` is System A's parsed value if present,
  else System B's — since exactly one side is `None` for `missing_in_b`/`orphan_ref`, and
  `None` for both means the row can't be sorted by value at all.
- **`None` sort_value placement**: rows with no comparable numeric value sort last
  regardless of ascending/descending direction (tuple key `(1, 0)` vs `(0, ±v)`) — a missing
  value is not "small," it's incomparable, so it shouldn't cluster at either extreme
  depending on direction.
- **Location name resolution** (`location_name`) is attached at this same response-shaping
  step, not stored on the disagreement — display-only enrichment, not part of the
  comparison or filter logic.

## Testing Decisions

- No dedicated test file exists yet for this seam specifically (see spec 04, Testing
  Decisions — same gap).
- If rewritten under TDD: red tests first for (a) `reason=value_mismatch` returns only that
  reason, (b) `sort=-value` returns strictly descending `sort_value`, (c) a
  `missing_in_b`/`orphan_ref` row (one side `None`) sorts using whichever side is present,
  (d) a mix including a fully-`None` row places that row last under both sort directions.

## Out of Scope

- Multi-field sort, free-text search, filter by location/org beyond the tenant boundary
  already enforced in spec 04 — brief states "filter by reason, sort by value: that is
  enough."
- Client-configurable page size / result limiting — not needed at 120 rows.

## Further Notes

None.
