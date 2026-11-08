# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 1 — baseline diagnostic

I first ran the untouched skeleton through the visible checker as a diagnostic.
It failed with `NotImplementedError`, confirming the harness was exercising this
file rather than an unrelated implementation.

## Revision 2 — reflected stencil hypothesis

Visible-only observations:

- The color-1 cells form a source stencil.  Each other nonzero cell is retained
  and the output completes a congruent reflected copy in that marker's color.
- For a left/right copy, the marker is paired with the **leftmost** color-1 cell
  in its row.  Reflecting every original color-1 coordinate across the midpoint
  of that pair reproduces all horizontal colored copies in the five examples.
- For an up/down copy, the marker is paired with the **topmost** color-1 cell in
  its column.  The analogous reflection reproduces all vertical copies.
- The one marker aligned both ways (train example 2, color 3) selects the shorter
  displacement, which is the vertical reflection.
- Copies can overwrite source cells or earlier copies.  Reading-order painting
  explains the color-7 overwrite of the color-2 copy in train example 4.
- Reflected coordinates outside the grid are clipped; the lower color-7 copy in
  train example 4 demonstrates this.

Program plan: retain the original color-1 coordinate set, enumerate markers in
row-major order, choose the aligned anchor/axis as above, paint the reflected
coordinates, and leave an unaligned unexpected marker unchanged.  Remaining
uncertainty is limited to unseen tie-breaking when a marker has equally short
valid row and column alignments; no visible query needs that case.
