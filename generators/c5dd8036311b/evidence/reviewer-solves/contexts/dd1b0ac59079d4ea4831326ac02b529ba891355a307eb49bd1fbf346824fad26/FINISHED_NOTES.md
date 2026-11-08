# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — color-specific upward masts

Earlier exposure: none known. I had not opened this task's generator, reference
rule, notes, solutions, audit records, or private labels before this attempt.

Visible evidence: each input has a horizontal row of color 1 with one or more
non-1 markers. In every training pair, a marker of color 2 gains a vertical mast
above it whose top is four rows above the marker: the top remains color 2 and the
three intervening cells become color 1. A marker of color 8 similarly gains a
mast whose top is three rows above it, with two intervening color-1 cells. The
base row and all unrelated cells stay unchanged. The heights are constant across
marker positions, counts, and grid widths in the visible examples.

Probe: I wrote a temporary visible-example test that imports `solution.py` and
compares `solve` against all three public training outputs. It first failed at
the untouched `NotImplementedError`, establishing the red test. The implementation
copies the grid, applies the two observed color-to-distance mappings to every
marker in the original grid, and does not inspect masked query labels.

Alternatives considered: height based on marker count or horizontal spacing is
contradicted by training example 0, where colors 2 and 8 occur equally often but
use different heights, and by examples 1–2, where color 2 keeps the same height
with three markers and one marker. Remaining uncertainty: the visible data only
establish mappings for colors 2 and 8; unseen marker colors are left unchanged.
