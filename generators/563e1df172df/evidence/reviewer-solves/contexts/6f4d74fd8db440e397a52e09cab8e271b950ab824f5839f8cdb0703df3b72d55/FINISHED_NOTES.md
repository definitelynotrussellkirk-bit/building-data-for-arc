# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — horizontal-then-vertical L path

Observed that every input has one red cell (2) and one green cell (3). In all
four examples, azure cells (8) trace the Manhattan path that starts at red,
travels horizontally on red's row until it reaches green's column, then travels
vertically on that column to green. The colored endpoints are preserved. The
corner is azure unless red and green already share a row and the corner is the
green endpoint.

I compared the coordinates and changed-cell counts manually:
- example 0: (7,1) -> corner (7,9) -> (8,9), eight azure cells;
- example 1: (4,14) -> (4,4) -> (8,4), thirteen azure cells;
- example 2: (8,1) -> (8,4) -> (6,4), four azure cells;
- example 3: (10,8) -> (10,4) -> (4,4), nine azure cells.

Alternative rejected: vertical first, then horizontal. Examples 1–3 visibly put
the long horizontal segment on red's row, so the turn order is determined.
Remaining uncertainty is limited to degenerate same-row/same-column inputs; the
implementation uses the natural endpoint-excluding path in those cases.
