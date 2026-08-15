# Disagreements Screen — Spec Index

This feature is split into six seam-scoped specs, each independently TDD-able. Build and
test in this order — each spec's tests must be green before the next spec's implementation
starts, since each layer is a real dependency of the next:

1. [`01-db-schema.md`](./01-db-schema.md) — tables, no logic. Tested via round-trip
   read/write, not TDD in the red-green sense (no behavior to drive).
2. [`02-importer.md`](./02-importer.md) — CSV → DB, survives dirty rows. TDD target:
   row-count-in == row-count-out.
3. [`03-comparison-engine.md`](./03-comparison-engine.md) — the core. Pure function, DB-free.
   TDD target: one red test per disagreement reason, written before the matching logic.
4. [`04-api-endpoints.md`](./04-api-endpoints.md) — wires DB rows into the comparison engine,
   enforces org scoping. Depends on 1–3.
5. [`05-filter-and-sort.md`](./05-filter-and-sort.md) — `reason` and `sort` query params on
   top of endpoint 4. Depends on 4.
6. [`06-frontend.md`](./06-frontend.md) — table UI consuming 4+5. Depends on all above.

## Cross-cutting decisions (apply to every spec below)

- **Never silently drop a row.** Any place data could be discarded (unparseable value,
  dangling reference, unmapped location) must fall back to a value the existing logic
  already knows how to handle (`None`, `UNRESOLVED`) — never a raise, never a skip. This
  rule is why specs 02 and 04 both mention fallback buckets: it's one rule applied twice,
  not two separate features.
- **Tenant boundary is real even though auth is out of scope.** `org_id` is always resolved
  server-side from `location_id`, never accepted as a claim from the client. This constrains
  specs 04 and 05.
- **Comparison logic must be testable without a database.** Spec 03's function takes and
  returns plain dicts. Specs 01/02/04 exist to feed it real data, but none of their tests
  substitute for spec 03's own unit tests.

## Riskiest assumption (spans specs 02 and 03)

`SystemB.value` is assumed to correspond to `SystemA.total_value` (not `base_value` or
`adjustment`) — inferred from sample rows, not confirmed against a data dictionary. If this
mapping is wrong, every `value_mismatch` finding from spec 03 is compromised regardless of
how well specs 01/02/04/05/06 are built. Documented as a known risk, not defended in code
(see spec 03, Out of Scope).

## Status

All six specs describe a system that is already implemented and tested (see
`backend/app/`, `backend/tests/`, `frontend/app/page.tsx`). These specs exist to make each
seam's contract explicit and independently re-driveable via TDD — e.g. if a seam is ever
rewritten, its spec's Testing Decisions section is the red-test checklist to satisfy before
touching the implementation.
