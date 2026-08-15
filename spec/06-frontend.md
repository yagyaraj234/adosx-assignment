# Frontend — Spec

Part of [00-index.md](./00-index.md). Depends on: 04, 05.

## Problem Statement

A reviewer needs a working screen to see disagreements, filter, and sort — without spending
the day on visual design, which the brief explicitly excludes ("plain and working beats
pretty and broken").

## Solution

A single Next.js page (`frontend/app/page.tsx`) — plain table, org selector, reason filter
with colored badges, ascending/descending value sort, and loading/empty/error states.

## User Stories

1. As a tenant user, I want to pick my org from a selector populated from `GET /api/orgs`,
   so that I never have to know or type an org ID.
2. As a reviewer, I want a table showing reason, both systems' values, and the location
   name (not a raw ID) for every disagreement, so that I can scan it without
   cross-referencing `locations.csv`.
3. As a reviewer, I want a reason filter with a colored badge per reason, so that different
   disagreement types are visually distinguishable at a glance without extra reading.
4. As a reviewer, I want to toggle value sort ascending/descending, so that I can find the
   largest discrepancies first.
5. As any user, I want a clear loading state while data is fetching, an empty state when a
   filter returns nothing, and an error state if the API call fails, so that the screen
   never looks broken or stuck when it's actually just empty or slow.

## Implementation Decisions

- **Plain table, no component library.** No design system, no CSS-in-JS framework — CSS
  variables and a scannable table structure only, per the brief's explicit "do not spend
  your day on CSS."
- **Org selector stands in for the tenant boundary.** Since auth is out of scope, the org
  selector is the only UI mechanism for choosing "who am I looking at this as" — it is not
  meant to imply real authentication.
- **Data flow**: org selection → `GET /api/orgs` (once, on load) to populate the selector;
  org + reason + sort → `GET /api/disagreements` (spec 04/05) refetched on any of the three
  changing.
- **`NEXT_PUBLIC_API_URL`** env override for the backend origin, defaulting to
  `http://localhost:8000` — the only configuration point, since deployment isn't in scope.

## Testing Decisions

- No frontend test suite — the brief's testing requirement is scoped to the comparison
  logic (spec 03), and the frontend was verified by manually driving the running app in a
  browser rather than by automated UI tests.
- **Regression caught this way, not by any automated test**: an early `normalize_ref` bug
  (spec 03) that turned one real match into two phantom disagreements was invisible to the
  passing pytest suite but obvious on sight in the rendered table (`REC-1112`/`1112` showing
  as two separate rows) — this is the concrete argument for at least one manual
  browser pass per change to this seam, even without a formal E2E suite.
- If a minimal automated check were added under TDD: a single smoke test (e.g. Playwright)
  asserting that selecting an org renders at least the expected column headers and that
  changing the reason filter changes the row count — not a full UI test suite, since visual
  design isn't graded.

## Out of Scope

- Visual design beyond a scannable plain table — explicitly excluded by the brief.
- Any automated frontend test suite (unit or E2E) — not required by the brief's testing
  criterion, which targets the comparison logic specifically.
- Pagination, virtualized scrolling — 120 rows total, not graded on performance.

## Further Notes

The `normalize_ref` bug described in Testing Decisions is the one concrete instance in this
whole project of a bug an automated test missed and a manual browser check caught — worth
citing directly if asked, in the follow-up call, why this seam has no automated test yet
still shipped a caught-and-fixed bug.
