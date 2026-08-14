# AdosX take-home: system disagreements

Finds the events where System A and System B disagree, scoped so one tenant never
sees another tenant's rows.

## How to run

Requires Python 3.11+ and Node 18+.

**Backend** (FastAPI + SQLite, port 8000):

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload
```

On startup it drops/recreates the SQLite DB and re-imports `data/*.csv` fresh every time —
no separate migration step.

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
  Every row is kept even when a value is blank, comma-formatted, or otherwise not a number —
  dirty fields are stored as their raw string plus a nullable parsed number, never dropped.
- **Comparison engine** (`backend/app/compare.py`): a single pure function, `find_disagreements`,
  that takes plain System A/B rows and returns every disagreement with its reason. No DB
  dependency, so it's directly unit-testable.
- **Four disagreement reasons**, per the brief: `missing_in_b`, `orphan_ref`,
  `duplicate_in_b`, `value_mismatch`. Reference matching survives three dirty `record_ref`
  formats (`REC-1034`, `rec1034`, `1112`).
- **API** (`backend/app/main.py`): `GET /api/orgs` and `GET /api/disagreements?org_id=...`
  (required) with optional `reason` filter and `sort`. `org_id` is resolved server-side
  through the `locations` table — a request can never see rows outside the org it asked for.
- **Frontend** (`frontend/app/page.tsx`): a plain table with an org selector (stands in for
  the tenant boundary, since auth is explicitly out of scope), a reason filter, and
  ascending/descending value sort.
- **Tests** (`backend/tests/test_compare.py`): one test per disagreement type, plus tests for
  the "no disagreement" case, epsilon tolerance, and each dirty `record_ref` format.

## What I deliberately did not build

- Authentication — explicitly out of scope per the brief.
- A 5th "location mismatch" disagreement category (System B carries its own `location_id`)
  — the brief asks for exactly four reasons; see DECISIONS #7.
- Visual design/CSS beyond a plain HTML table — explicitly out of scope.
- Migrations tooling (Alembic) — the schema is fixed and the dataset is static; see DECISIONS #3.
- Pagination, loading skeletons, or any performance work — 120 rows per file, not graded.
- A runtime check for `record_ref` normalization collisions — checked the data by hand and
  found none; see DECISIONS #4.

## How I worked with the agent

I ran a structured interview first (stack, schema, matching/dedup rules, value tolerance,
and — the trickiest part — how to prove tenant isolation without building auth) before any
code was written, so the agent had a fully-settled spec rather than guessing mid-build. It
then implemented the importer, comparison logic, API, and frontend, wrote the pytest suite,
and independently drove the running app in a real browser (not just curl) to verify the
tenant filter, reason filter, and sort actually worked end to end — that browser check is
what surfaced the bug described below.

### a. Name one thing the AI agent got wrong. How did you notice?

The first version of `normalize_ref` only handled two of the three dirty `record_ref`
formats in the data (case-insensitive, dash-insensitive) but required a `REC` prefix, so it
rejected the bare-digit variant (`"1112"` for `REC-1112`). That silently turned one real
match into two false disagreements — a phantom `orphan_ref` for `"1112"` and a phantom
`missing_in_b` for `REC-1112`. I didn't catch it from the passing test suite (the tests
didn't cover that specific dirty variant); I noticed it by loading the actual running app in
a browser and reading the rendered rows, where `REC-1112`/`1112` showing up as two separate
rows looked wrong on sight. Fixed by widening the regex to accept an optional `REC` prefix,
then added a regression test for it.

### b. Which part of your submission are you least confident about, and why?

The value comparison assumes System B's `value` column corresponds to System A's
`total_value` specifically (not `base_value` or `adjustment`) — I confirmed this by eyeballing
a handful of agreeing sample rows where `base_value + adjustment = total_value = value`, but
that's inference from a sample, not something stated in the data dictionary. If that mapping
is wrong, every `value_mismatch` finding is compromised. The 0.01 epsilon tolerance is
similarly a reasonable-sounding guess for money values rather than a specified requirement.

### c. If you had a second day, what would you fix first?

I'd add an importer-level test that asserts row count in equals row count out regardless of
CSV content (currently proven by manual inspection, not asserted in code), then add the
normalization-collision check I skipped in DECISIONS #4, then improve the frontend with
proper loading/error states and an env-based API URL for a real deployment.
