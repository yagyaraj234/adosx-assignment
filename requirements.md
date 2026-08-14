AdosX ENGINEERING
Full-Stack Engineer
Take-home brief
Time box
About one working day. Return within three days of receiving this.
Format
A working feature, back to front.
Stack
Django and React or Next.js preferred. If you are strong elsewhere, tell us and use it.
AI agents
Encouraged. Read the section on this before you start.
Attached
system_a.csv, system_b.csv, locations.csv

Context
We have two systems record the same events. Neither is authoritative. They agree on most rows and disagree on a few dozen, and those few dozen are the ones anyone actually cares about. They are also spread across multiple tenants, and a row belonging to one tenant must never be visible to another.
Find the disagreements. Do not leak across the boundary.
The data
Three files, attached:
system_a.csv. One row per event, as System A recorded it. record_id is the identifier.
system_b.csv. One row per entry, as System B recorded it. record_ref points back at System A, and it is not always clean. There may be more than one entry per record.
locations.csv. Every location belongs to exactly one org. This file is the only place that mapping exists. Org means tenant.
120 rows on each side. Small enough to read with your eyes, dirty enough to hurt. Every ugly thing in it is deliberate. Assume real exports are worse.
The task
Build a screen that shows the records where the two systems disagree.

1. Load the data
   Import both CSVs into a database. Design the tables yourself; we want to see how you think about them.
   The data is dirty. Values that are not parseable numbers, blank fields, references written three different ways, an entry that points at a record that does not exist. Your importer must survive all of it without silently dropping rows.
2. Compare them
   Match each System A record to its System B entry and flag the ones that do not agree. At minimum, catch these:
   A record in System A with no entry in System B.
   A System B entry pointing at a record that does not exist.
   The same record entered into System B twice.
   The two systems reporting different values for the same record.

3. Show them
   A table listing every disagreement, with the reason, both systems' versions of the value, and the location.
   Filter by reason. Sort by value. That is enough.
   Plain and working beats pretty and broken. Do not spend your day on CSS.
4. Test it
   Write tests for the comparison logic. Not for everything, just for the part where the disagreements are decided.
   For each kind of disagreement you catch, one test that proves you catch it.
   What to submit
   A private Git repository, with us added as collaborators. Commit as you go. We look at the commit history, so please do not squash a day of work into one commit.
   A README that covers: how to run it, what you built, what you deliberately did not build, and the How I worked with the agent section.
   A DECISIONS file, three to ten short entries. Each entry: the decision, the alternative you rejected, and the one line of reasoning that separated them.
   Answer these three questions at the bottom of your README, in a few sentences each.
   a. Name one thing the AI agent got wrong. How did you notice?
   b. Which part of your submission are you least confident about, and why?
   c. If you had a second day, what would you fix first?
   How we evaluate
   Criterion
   What we are reading for
   Weight
   Correctness
   Does it run from a clean clone, and does it find the disagreements it claims to find.
   30%
   Handling the mess
   Dirty rows survive the importer. Nothing is silently dropped. The non-error is correctly identified as a non-error.
   25%
   Working with the agent
   Your three README answers, and whether you can defend your own code on the call. This carries real weight for a junior role.
   20%
   Tests
   Do they test the thing that matters, and would they catch a regression.
   15%
   Clarity
   Can we read your code and your README without asking you what you meant.
   10%

What we are not testing
So you can spend your day on the parts that count:
Visual design. A plain table is the correct answer.
Authentication. Skip it entirely.
Performance. Each file has a hundred and twenty rows.
Finishing everything. See the note on scope at the end.
Using AI agents
Use them. Claude Code, Cursor, Copilot, whatever you already work with. This is how we build every day, and a junior who works well with an agent is more useful to us than one who refuses to.
So: use the agent freely, and check its work relentlessly. In the follow-up call we will open a file you submitted, point at a function, and ask you why it is written that way.

A note on scope
This is deliberately larger than one day of work. That is the point. We want to see what you cut, and whether you cut the right things. A small, complete, well reasoned slice with an honest list of what you left out beats a sprawling half working submission every time.
If something in the brief is ambiguous, do email us or make a call and write it down in DECISIONS, and move on.
