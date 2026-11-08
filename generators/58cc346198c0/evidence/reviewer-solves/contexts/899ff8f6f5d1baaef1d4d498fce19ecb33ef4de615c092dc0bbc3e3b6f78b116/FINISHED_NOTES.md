# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1

Observed that every nonzero 4-connected object is replaced by the four corners of
its axis-aligned bounding rectangle, using the object's original color. The first
example has a gray staircase with bounding box rows 0–2, columns 1–4, and the
output places gray at exactly those four corners; the azure L object behaves the
same way. The other examples confirm separate same-color objects are processed
independently. A single-row or single-column box naturally produces two unique
corner cells, and a one-cell object stays one cell.

Before implementation I ran a visible-example assertion harness against the
provided stub and observed the expected `NotImplementedError`. I then implemented
4-neighbor flood fill, collected each component's row/column extrema, and wrote
its corners into a zero grid of the original dimensions. Remaining uncertainty:
whether the hidden generator ever makes same-color objects touch only diagonally;
the visible examples support standard 4-connectivity.
