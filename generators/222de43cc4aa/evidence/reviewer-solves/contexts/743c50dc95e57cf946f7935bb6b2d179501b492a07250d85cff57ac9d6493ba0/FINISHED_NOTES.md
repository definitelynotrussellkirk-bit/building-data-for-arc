# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Attempt 1 — reflected vertical continuation

**Earlier exposure:** none to this task's rule, generator, notes, solutions, or labels.
I only read the visible examples printed by `review.py blind prepare`.

**Observation.** In every training pair, the first `h` output rows exactly equal
all `h` input rows. The remaining output rows are existing input rows; no row is
recolored or shifted. Their source-row indices form the same triangular walk:

- for `h = 5`: `0,1,2,3,4,3,2,1,0,1,2,3,4,3,2,1,0`;
- for `h = 6`: `0,1,2,3,4,5,4,3,2,1,0,1,2,3,4,5,4,3,2,1,0`.

So the transformation is two complete top-to-bottom-to-top reflected traversals,
with turning rows included once. It preserves width and produces `4*h - 3` rows.
The colors and horizontal periodicity are irrelevant to the operation.

**Implementation.** Copy rows according to
`0..h-1`, `h-2..0`, `1..h-1`, `h-2..0`. I also handle empty and one-row inputs
conservatively, although neither appears in the visible examples.

**Remaining uncertainty.** The examples strongly determine the row-index walk,
but only heights 5 and 6 are visible. The generic implementation assumes the same
reflection rule at other legal heights rather than a fixed 17/21-row target.
