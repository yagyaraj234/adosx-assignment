# Comparison Engine — Spec

Part of [00-index.md](./00-index.md). Depends on: nothing at runtime (pure function; fed
by 02's output via 04). Depended on by: 04.

This is the core of the feature — the part the brief explicitly singles out for testing
("test the part where the disagreements are decided").

## Problem Statement

Given System A's records and System B's entries, decide which records the two systems
disagree on and why, in a way that's testable without a database, a fixture, or a running
app.

## Solution

`find_disagreements(system_a_rows, system_b_rows)` (`backend/app/compare.py`) — a pure
function over plain dicts in, plain dicts out. No SQLModel objects, no DB session.

## User Stories

1. As an engineer, I want the comparison logic as a pure function with no DB dependency, so
   that I can unit test the matching/dedup/tolerance rules directly, in isolation, at unit
   speed.
2. As an operator, I want a System A record with no matching System B entry flagged
   `missing_in_b`.
3. As an operator, I want a System B entry whose `record_ref` matches no System A record
   flagged `orphan_ref`.
4. As an operator, I want two or more System B entries matching the same System A record
   flagged `duplicate_in_b`, grouped into one disagreement row with every B value shown.
5. As an operator, I want a System A/B pair whose values differ by more than a small
   tolerance flagged `value_mismatch`.
6. As an operator, I want `record_ref` values written as `REC-1034`, `rec1034`, or `1112` to
   all resolve to the same System A record, so formatting noise never manufactures a false
   `orphan_ref`/`missing_in_b` pair.
7. As an operator, I want values within 0.01 of each other treated as agreeing, so that
   float round-tripping through CSV doesn't manufacture a false `value_mismatch`.

## Implementation Decisions

- **Signature**: `find_disagreements(system_a_rows: list[dict], system_b_rows: list[dict])
  -> list[dict]`, where each output dict has `reason`, `record_ref`, `location_id`,
  `system_a_value`, `system_b_value`, `entry_ids`.
- **Ref normalization** (`normalize_ref` in `backend/app/parsing.py`): case-insensitive,
  dash-insensitive, optional `REC` prefix — collapses `REC-1034`/`rec1034`/`1112` to one
  key. Chosen over strict-pattern matching after finding the bare-digit variant in the real
  data; under-matching was judged worse than over-matching (see [00-index.md](./00-index.md),
  cross-cutting decisions).
- **Matching**: build `ref -> A row` and `ref -> [B entries]` maps, then for each A ref:
  zero B entries → `missing_in_b`; exactly one → compare values; two or more →
  `duplicate_in_b` (all B values joined for the row). For each B ref with no A row →
  `orphan_ref`.
- **Value tolerance**: `abs(a - b) <= 0.01`; both `None` counts as agreement, one `None`
  counts as disagreement (folds unparseable values into `value_mismatch` — see spec 02).
- **Field mapping assumption**: `SystemB.value` is compared against `SystemA.total_value`,
  not `base_value` or `adjustment` — inferred from sample rows, not a confirmed data-
  dictionary fact. See [00-index.md](./00-index.md) for why this is the single riskiest
  assumption in the whole feature.
- **One reason per record, priority order duplicate > value_mismatch**: a duplicated B
  entry that also disagrees in value is still reported as `duplicate_in_b`, not
  additionally as `value_mismatch` — the duplicate itself is the more actionable problem to
  surface first.

## Testing Decisions

`backend/tests/test_compare.py` — the priority test suite for this whole feature.

- One test per reason: `missing_in_b`, `orphan_ref`, `duplicate_in_b`, `value_mismatch`.
- One "no disagreement" control case (proves the function doesn't over-fire).
- One test per dirty `record_ref` variant (case, dash, bare-digit) — this is the exact spot
  where a real regression happened (a first pass rejected the bare-digit variant, turning
  one true match into two phantom disagreements); each variant gets its own test so this
  class of bug can't recur silently.
- One test for the 0.01 epsilon boundary (just-inside passes, just-outside flags).
- TDD order: write all four reason tests red (against a stub/empty `find_disagreements`)
  before writing any matching logic — the four reasons are independent branches and can be
  driven one at a time.

## Out of Scope

- A 5th "location mismatch" reason, even though System B carries its own `location_id` that
  could differ from System A's — brief specifies exactly four reasons.
- A runtime assertion that `base_value + adjustment == total_value` to defend the field-
  mapping assumption above — documented as risk instead (see
  [00-index.md](./00-index.md)).
- A runtime check for `record_ref` normalization collisions across the dataset — checked by
  hand once, none found; not automated.

## Further Notes

None.
