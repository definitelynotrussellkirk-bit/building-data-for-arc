# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — untouched-stub diagnostic

I first ran the checker against the supplied `NotImplementedError` stub to make
sure the visible-feedback path was active.  It errored on all three examples;
this was a diagnostic probe, not a proposed rule.

## Revision 2 — marked-axis mirror completion

All cells of color 8 are collinear.  In examples 0 and 2 they share a row; in
example 1 they share a column.  Treat that row or column as a reflection axis.
Reflect every non-background, non-8 cell from the original input across the
axis.  Copy its color only when the reflected coordinate is in bounds and the
target is 0, so a pre-existing contradictory-colored cell is not overwritten.

Checks against the examples by hand:

- Example 0: the lower cells at rows 5 and 6 create the missing rows 1 and 0;
  the row-4 color would land on an already occupied row-2 cell and is preserved.
- Example 1: only `(1, 3)` has an in-bounds reflection across column 2, adding
  `(1, 1)`.
- Example 2: the pattern above row 3 is copied below it.

I considered copying only the visually fuller side, but a one-pass symmetric
closure of the original colored cells is simpler and gives exactly the same
visible outputs while handling partial content on either side.  Remaining
uncertainty: the hidden queries could distinguish one-way copying from symmetric
closure if both sides contain unmatched in-bounds cells.  The examples support
preserving all originals and filling all empty reflected positions.
