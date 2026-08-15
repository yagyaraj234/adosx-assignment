# API Endpoints — Spec

Part of [00-index.md](./00-index.md). Depends on: 01, 02, 03. Depended on by: 05, 06.

## Problem Statement

The comparison engine (spec 03) knows *which* records disagree; it has no notion of
tenants. The API must feed it real DB rows (spec 01/02) and enforce that a request for one
org never returns another org's rows — without building authentication, which is out of
scope.

## Solution

Two read-only FastAPI endpoints (`backend/app/main.py`) — `GET /api/orgs` and
`GET /api/disagreements` — that resolve `org_id` server-side via a join through the
`locations` table, never from a client-supplied claim.

## User Stories

1. As a tenant user, I want to pass `org_id` as a required query parameter and get back only
   disagreements whose location belongs to that org, so that I can never see another
   tenant's rows by omission or by guessing a different `org_id`.
2. As a tenant user, I want a disagreement whose `location_id` isn't in `locations.csv` at
   all to appear under a synthetic `UNRESOLVED` org rather than disappear, so that a gap in
   the location mapping doesn't silently hide a real disagreement from every tenant (same
   "never silently drop" rule as spec 02, applied to org resolution instead of parsing).
3. As a frontend, I want `GET /api/orgs` to list every real org plus `UNRESOLVED` if it's
   ever triggered, so that the org selector (spec 06) never needs a hardcoded list.
4. As a client, I want an unknown `org_id` to return 404, not an empty/silent 200, so that a
   typo or bad request is visible instead of looking like "this tenant has zero
   disagreements."

## Implementation Decisions

- **`GET /api/orgs`**: returns every distinct `org_id` from `locations`, plus `UNRESOLVED`
  if any System A/B row references a `location_id` absent from `locations.csv`.
- **`GET /api/disagreements?org_id=...`**: `org_id` is a required query param (no default,
  never inferred). Loads all A/B rows, all locations; calls `find_disagreements` (spec 03)
  once; then filters the result down to rows whose `location_id` maps (via `locations`) to
  the requested `org_id` — a `location_id` with no mapping resolves to `UNRESOLVED`, not
  `None`, so it lands in a real bucket instead of being un-filterable.
- **Location source per reason**: for `orphan_ref` (no A row exists), `location_id` comes
  from the B entry; for every other reason, from the A row. This is a real, intentional
  asymmetry, not an inconsistency — there's no A row to prefer in the orphan case.
- **Unknown `org_id` → 404**, checked against `known_orgs = {locations' org_ids} |
  {UNRESOLVED}` before filtering, not inferred from "zero rows returned."
- **CORS**: locked to `http://localhost:3000` (the frontend's dev origin) — not
  configurable, since auth/deployment hardening is out of scope.
- **No pagination** — 120 rows total across both files, not graded on performance.

## Testing Decisions

- Exercised indirectly today via the frontend's manual browser verification (see spec 06,
  Further Notes) — no dedicated `test_main.py` exists yet, since the brief's testing
  requirement is scoped to spec 03's comparison logic specifically.
- If this seam is rewritten under TDD: red tests first for (a) `org_id` required → 422 with
  it omitted, (b) unknown `org_id` → 404, (c) a disagreement whose location resolves to org
  X is absent when querying org Y, (d) an `UNRESOLVED`-bucket disagreement is retrievable by
  querying `org_id=UNRESOLVED`. Use `TestClient` against an in-memory/temp SQLite DB seeded
  with a small fixture, not the real `data/*.csv`.

## Out of Scope

- Authentication/session/login — explicitly excluded by the brief; `org_id` being a plain
  query param is the accepted tenant-boundary mechanism for this exercise (see
  [00-index.md](./00-index.md)).
- Write endpoints (create/update/delete) — the brief only asks for a read-only disagreements
  view.
- Rate limiting, request logging, observability — out of scope for a 120-row take-home.

## Further Notes

None.
