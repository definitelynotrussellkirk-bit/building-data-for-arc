# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — stable row compaction

Earlier exposure: none. Before this solve I had not opened this task's generator,
rule, notes, solutions, audit records, or the assigned repair generator.

Observation: every training output keeps the same height and width, and each row
retains exactly the same nonzero colors in the same left-to-right order. The only
change is that zeros between or before colored cells are removed and the displaced
zeros are appended at the row's right edge. Rows are independent; empty rows stay
empty.

Hypothesis: for each row, collect all nonzero entries in original order, place them
starting at column zero, and fill the remaining cells with zero. This predicts, for
example, query 0 row 0 as `[9, 1, 4, 0, 0, 0, 0, 0]` and query 1 row 3 as
`[9, 1, 8, 0, 0, 0, 0, 0, 0, 0]`.

Probe: a visible-example harness first failed on the untouched scaffold with
`NotImplementedError`, confirming it exercised `solve`. I then implemented only the
row-wise stable compaction rule. Alternatives considered and rejected: sorting by
color (training order is preserved), column-wise gravity (rows do not exchange
cells), or global packing (nonzeros remain on their original rows).
