# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Prior exposure

I had already inspected this task's generator and rule authority while carrying
out the assigned repair, so this is **not** a blind solve.  During this solve
phase I did not reopen those sources, reference solutions, or private labels.
I based the implementation below on the newly materialized visible examples.

## Revision 1 — directed marker translation

Hypothesis: locate the connected color-2 object, compute the displacement from
the unique 8 cell to the unique 9 cell, and paint a translated copy of every
color-2 cell in color 3.  Retain the original grid and clip translated cells
that leave the canvas.  Other colors appear to be irrelevant decorations.

Visible probes:

- Example 0 has vector `(0,+5)` and moves the three vertical color-2 cells from
  column 4 to column 9.
- Example 1 has vector `(+3,-5)` and the four output-3 cells equal the four
  source coordinates plus that vector.
- Example 2 has vector `(+5,0)`; only two translated cells remain inside the
  10-row canvas, directly demonstrating clipping rather than rejection.

Before implementing, I ran a small visible-example regression against the
skeleton and observed the expected `NotImplementedError`.  I then implemented
the direct coordinate translation.  No competing visible rule explains all
three directional cases as simply; the first example also rules out a
"diagonal vectors only" condition because its horizontal vector is active.
