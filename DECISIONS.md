1. FastAPI + Next.js

used FastAPI + Next.js, not Django.

I choose FastAPI over Django because i never worked on Django and this task is all about just dummy data with some api endpoints. also i have worked in FastAPI so i thought just go with FastAPI with this i can move fast.

django would work. it just solves problems this project does not have.

2. sqlite resets on every startup

the database is dropped, recreated, and imported from the three CSVs on every boot. no alembic.

this database is not the source of truth. it is derived data. nothing accumulates in it, there is no state to migrate, and deleting it loses nothing.

i rejected postgres and docker-compose because the clean-clone run is graded. pip install && uvicorn has fewer ways to fail on an unfamiliar machine than a container setup does.

3. record_ref matching is deliberately forgiving

matching ignores case, dashes, spaces, and prefixes.

the file contains rec1034, " REC - 1070 ", and bare 1112. strict REC-#### matching would turn one real agreement into two disagreements. for a screen that is supposed to find real disagreements, under-matching is the more expensive mistake.

an unparseable ref gets its own key. it does not go into a shared None bucket, because then every broken ref appears to match every other broken ref. that is a silent misclassification inside the one function that cannot afford to lose rows.

4. multiple B entries are not automatically duplicates

if several System B entries add up to System A's value, that is a split.

REC-1055 has 71950.93 + 107926.39, exactly equal to A's 179877.32. one row says Entry part 2 of 2, but the arithmetic is the decision. labels are free text, and one example is not a schema.

REC-1042 repeats 112837.06 twice. that is a real duplicate.

i rejected treating every multi-entry record as a duplicate because the brief says there may be more than one entry per record. real duplicates collapse into one row per record with every value shown, since comparing the values side by side is the point of the row.

5. a voided A record should be absent from B

if System A says VOIDED, System B being absent is correct. if B still has the record, it is voided_in_a.

the first version ignored state. that made REC-1019, the only voided row in the 120-row dataset, report nothing at all.

the opposite interpretation is worse: a voided row with a matching B value becomes a non-error even though the systems disagree on whether the event happened. one row is not enough evidence to know what System B intended, so i chose to surface it rather than hide it.

6. location_mismatch is a fifth reason

the brief says to catch four reasons at minimum. four is the floor.

REC-1077 is LOC-102 / ORG-A in System A and LOC-201 / ORG-B in System B. the values match. under only four reasons, the record looks clean and disappears for everyone even though the two systems disagree about ownership.

both tenants see the row because both are involved. both see the disputed value. the other side is redacted: no location id, no location name, no System B entry_id.

the counterparty identity is private. the disagreement itself is not.

7. visibility checks every location the row touches

a tenant can see a disagreement if any location involved belongs to them.

filtering only by System A's location_id assumes A is correct about ownership. REC-1077 is exactly the case where that assumption fails.

redaction goes through one helper, not a check per field. a location name cannot come back without its id passing the same test. the System B entry_id that was still leaking on REC-1077 got caught because the test checks the rule, not the field.

a location_id missing from locations.csv resolves to a synthetic UNRESOLVED org instead of None. a None org matches no filter, so the row would just vanish. UNRESOLVED keeps it reachable by somebody.

8. the importer commits row by row

every row goes in on its own savepoint. rows the database refuses come back as a list and get printed at startup with the file and line number.

the first version added all 361 rows and committed once at the end. one truncated line hits NOT NULL, one repeated id hits UNIQUE, and either one takes the entire import down. that is the loudest possible way to fail "nothing is silently dropped".

a missing column or a short row becomes an empty string instead of a KeyError or a NULL.

i rejected surrogate primary keys as the fix. it strips the meaning out of three tables' keys, and it needs a second fix for duplicate location_id rows, to remove a failure the reject report already names by file and line.

9. the comparison function is plain dicts in, plain dicts out

no session, no ORM objects, no org filtering.

REC-1055 and REC-1077 are both four-line dicts in a test file. if find_disagreements took a Session, testing the split-sum case would need a database standing up first. the brief singles out this function as the part to test, so it should be the easiest thing in the repo to test.

org filtering stays in the API on purpose. a disagreement can straddle two tenants, so this is not the layer that can decide who sees it.

10. value comparison uses a 0.01 tolerance

i checked whether it does anything, and on this data it does not. every value on both sides has exactly two decimal places, and all 113 agreeing pairs are byte identical. exact equality would pass every test in the repo.

i kept it anyway. the comparison runs on floats parsed from text, and the risk is one-sided. a re-export written to more precision gives a screen full of phantom mismatches. a tolerance one paisa wide hides nothing worth seeing.
