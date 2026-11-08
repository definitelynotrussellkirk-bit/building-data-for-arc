# Solve work log

## Exposure declaration before solving

I did not open this task's generator, Racket rule, notes, solutions, audit
records, or private labels. I used only the public grids printed by
`python3 review.py blind prepare` and the visible-only checker.

## Revision 1 — mark membership in solid 2x2 color-2 blocks

**Hypothesis.** Locate every all-color-2 2x2 window. Recolor to 3 the union of
all color-2 cells participating in at least one such window. Preserve color-2
protrusions that are not in any qualifying 2x2, and preserve every other color.

**Evidence from the visible examples.**

- Train 0 has two isolated 2x2 blocks, both recolored, while the lower L-shaped
  triomino contains no full 2x2 and stays color 2.
- Train 1's upper-left object contains overlapping 2x2 windows. Every cell in
  their union becomes 3, but its one-cell tail at `(4,0)` stays 2. The separate
  2x2 becomes 3; the hollow 3x3 ring has no solid 2x2 and stays 2.
- Train 2's lower-left object contains a solid 3x3 region plus a one-cell
  extension. The 3x3 region is exactly the union of its four 2x2 windows and is
  recolored, while the extension stays 2. The separate 2x2 is recolored and the
  irregular upper object is unchanged.
- Non-2 2x2 objects (colors 7 and 4) remain unchanged, so the rule is specific
  to color 2 rather than generic square detection.

**Alternatives rejected.** Recoloring whole connected components fails on the
unrecolored tails in trains 1 and 2. Recoloring rectangles or largest objects
fails across examples. Recoloring every square-shaped component misses the 3x3
subregion embedded in a larger component.

**Remaining uncertainty.** None material for the visible domain: overlapping
2x2 windows are handled by set union and boundary windows are naturally scanned.
