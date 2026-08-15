# AdosX take-home: system disagreements

Finds the events where System A and System B disagree, scoped so one tenant never
sees another tenant's rows.

## How to run

Developed and tested on Python 3.14 and Node 24.

**Backend** (FastAPI + SQLite, port 8000):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On startup it drops/recreates the SQLite DB and re-imports `data/*.csv` fresh every time —
no separate migration step. It prints one line per row the database refused, then a total
(`[import] 0 row(s) rejected` on the supplied data).

**Run the tests:**

```bash
cd backend
.venv/bin/pytest -q
```

**Frontend** (Next.js, port 3000):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000. Backend must be running on :8000 first (override with
`NEXT_PUBLIC_API_URL`).

## What I built

- **Importer** (`backend/app/importer.py`, `parsing.py`): loads all three CSVs into SQLite.
  Dirty fields are stored as their raw string plus a nullable parsed number, so a blank,
  comma-grouped or plain unparseable value never costs a row. A missing column or a
  truncated line becomes an empty string rather than a `KeyError` or a `NOT NULL` failure,
  and each row is inserted on its own savepoint — a row the database genuinely refuses is
  reported by id and line number instead of aborting the whole file.
- **Comparison engine** (`backend/app/compare.py`): a single pure function,
  `find_disagreements`, taking plain System A/B rows and returning every disagreement with
  its reason. No DB dependency, so it is directly unit-testable. It deliberately does no
  org filtering — a disagreement can straddle two tenants, so that call belongs to the API.
- **Seven reasons.** The four the brief names — `missing_in_b`, `orphan_ref`,
  `duplicate_in_b`, `value_mismatch` — plus three the data forces:
  - `duplicate_in_a` — two System A records normalizing to one reference, so there is no
    single row left to compare against.
  - `location_mismatch` — the values agree but the systems filed the record under
    different locations, and therefore possibly different tenants (`REC-1077`).
  - `voided_in_a` — System A voided the record but System B still has an entry for it
    (`REC-1019`).
- **Two non-errors that look like errors.** Multiple System B entries whose values *sum*
  to System A's total are a split, not a double entry (`REC-1055`); a voided record with
  no System B entry is the expected outcome, not a `missing_in_b`. See DECISIONS #4 and #5.
- **Reference matching** survives four dirty `record_ref` formats (`REC-1034`, `rec1034`,
  `" REC - 1070 "`, bare `1112`), and a reference that will not normalize gets a bucket of
  its own so unparseable references never appear to match each other.
- **API** (`backend/app/main.py`): `GET /api/orgs` and `GET /api/disagreements?org_id=...`
  (required) with optional `reason` filter and `sort`. A disagreement is visible to a
  tenant if *any* location it touches belongs to that tenant, and every location goes
  through one redaction helper — so a contested row reaches both tenants while neither
  learns the other's location, location name, or System B entry id. An unknown `org_id` is
  a 404 and an unknown `reason` a 400, never a silently empty table.
- **Frontend** (`frontend/app/page.tsx`): a table with an org selector (stands in for the
  tenant boundary, since auth is explicitly out of scope), a reason filter with colored
  badges, ascending/descending value sort, and loading/empty/error states. Cached rows are
  reused across filter and sort changes but never across an org change.
- **Tests** (`backend/tests/`, 30 of them): one per disagreement reason, one per
  non-error, plus epsilon tolerance, each dirty `record_ref` format, and the no-collapse
  rule for unnormalizable and blank references. Four importer tests cover a dirty row, a
  truncated row, a missing column, and a row the database rejects. `test_api_tenancy.py`
  runs the real app against the real CSVs and asserts no other tenant's `location_id`
  appears *anywhere* in a response — not just in the location fields — which is what
  caught the System B `entry_id` crossing the boundary on `REC-1077`.

## What I deliberately did not build

- Authentication — explicitly out of scope per the brief.
- Heavy visual design (component library, animation, theming beyond CSS variables) —
  explicitly out of scope; the table itself is still plain.
- Migrations tooling (Alembic) — the schema is fixed and the dataset is static; DECISIONS #2.
- Pagination, indexes, or any performance work — 120 rows per file, not graded.
- Surfacing the importer's reject list in the UI. It goes to stdout at startup; on this
  dataset it is always empty, and an endpoint plus a screen for it is a day-two item.
- Reconciling System A's own `base_value + adjustment` against `total_value`. It holds for
  all 120 rows, so there was nothing to report; the brief asks about disagreement between
  the systems, not within one.

## How I worked with the agent

I ran a structured interview first (stack, schema, matching/dedup rules, value tolerance,
and — the trickiest part — how to prove tenant isolation without building auth) before any
code was written, so the agent had a settled spec rather than guessing mid-build. It then
implemented the importer, comparison logic, API, and frontend, wrote the pytest suite, and
drove the running app in a real browser to verify the tenant filter, reason filter and sort
worked end to end.

The pattern that actually caught bugs was checking the agent's output against the raw CSVs
rather than against its own tests. A passing suite only proves the code does what the code
was written to do; the traps in this dataset are all cases where the code was confidently
doing the wrong thing.

### a. Name one thing the AI agent got wrong. How did you notice?

It classified `REC-1055` as `duplicate_in_b`. System B has two entries for it, so the rule
it wrote — more than one entry means duplicate — fired, and every test passed, because the
tests were written from the same wrong rule. I noticed by reading the rows the screen was
showing rather than the tests: the two values were `71950.93` and `107926.39`, which are
not the repeated value a real double entry produces, and adding them gives `179877.32` —
System A's total, exactly. One of them is labelled "Entry part 2 of 2". It is a record
entered in two parts, and the brief says so directly: "there may be more than one entry per
record." `REC-1042`, whose two entries repeat `112837.06`, is the real duplicate.

The same check turned up two more: `location_mismatch` (`REC-1077`, filed under a different
tenant by each system, invisible to both because their values agree) and `voided_in_a`
(`REC-1019`, the only `VOIDED` row — a column the comparison was not reading at all).

### b. Which part of your submission are you least confident about, and why?

The split-entry rule in DECISIONS #4. It decides on a sum, and a sum is weak evidence: any
two entries that happen to add to System A's total will be waved through as a legitimate
split, including a genuine double entry of a record whose value is exactly half. It is
right on this dataset and corroborated by the label, but the real fix is a field in System
B that states which part of what an entry is, which this export does not have.

Second, the `voided_in_a` reading. I treat "voided in A but still live in B" as a
disagreement; someone could equally argue System B lags System A's voids by design and the
row is noise. There is one such row in the data, so I cannot tell from the data which it is.

### c. If you had a second day, what would you fix first?

Confirm the two judgement calls above with whoever owns System B — the split rule and the
voided reading are both places where I picked a reading and wrote it down rather than knew.
After that: surface the importer's reject list in the UI instead of stdout, and decide the
policy on `location_mismatch` values properly. Right now both tenants see the disputed
value on the theory that ownership is exactly what is unknown, which is defensible but is a
policy decision I made alone.
