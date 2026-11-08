# Blind solve work log — 97bcb3b9194e

This is a human-visible-example work log. I did not inspect the generator, Racket rule,
private labels, earlier solutions, or audit records.

## Observations

- Every input contains several nonzero rectangular panels separated by color 0.
- Color 1 is the common panel fill; colors 4 or 6 are exceptional cells retained in
  the selected output.
- The output is an exact crop of one panel, not a repaired or recolored panel.
- In training example 1, the selected panel has 1 non-1 cell versus 6 and 6.
- In training example 2, it has 2 non-1 cells versus 6 and 6.
- Training example 3 is the useful discriminator: the 3x3 distractor has six color-4
  cells, while the selected 5x10 panel has only three. Treating each object's own mode
  as its base would create a misleading tie, so the base must be the input's common
  nonzero fill (color 1), not each object's local mode.

## Hypothesis

Split the input into 4-connected nonzero components, crop each component's bounding
box, and return the crop with the fewest cells different from the globally dominant
nonzero color. Preserve all colors. For an unseen tie, prefer the larger panel and
then reading order; no visible example depends on this tie-break.

## Probe

A local script enumerated component bounds and exception counts. The selected counts
were 1, 2, and 3 across the three visible training examples, and the resulting crops
matched all visible outputs. The two test inputs have unique minima of 1 and 2.
