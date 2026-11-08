# Solve work log

## Exposure and constraints

Before solving I had read only the packet-level workflow and the visible challenge presentation. I did **not** inspect this task's generator, Racket rule, canonical record, prior solution, private labels, or audit evidence.

## Revision 1 — corner markers become inward glyphs

**Observation.** Every non-background input cell lies at a corner. The output clears the border markers and places a fixed glyph inward from each occupied corner, preserving that marker's color. Across all three demonstrations, top-corner markers become a 2×2 block one cell in from both adjacent borders. Bottom-corner markers become a three-cell bent stroke: two vertical cells at rows `H-4,H-3`, then one cell one step farther inward at row `H-2`. The right-side versions are horizontal reflections of the left-side versions.

**Coordinate formulas.** With height `H` and width `W`:

- top-left: `(1,1),(1,2),(2,1),(2,2)`
- top-right: `(1,W-3),(1,W-2),(2,W-3),(2,W-2)`
- bottom-left: `(H-4,2),(H-3,2),(H-2,3)`
- bottom-right: `(H-4,W-3),(H-3,W-3),(H-2,W-4)`

The dominant color is treated as background so the code does not hard-code color 7, although all visible examples use 7.

**Alternatives considered.** I checked whether glyph shape might depend on marker color or the number of occupied corners. Repeated colors in train examples 1 and 2 rule that out: the same color produces a 2×2 glyph at the top and a three-cell glyph at the bottom. The shape is therefore corner-position dependent.

**Probe.** A local test imported `solution.py` and compared its output against all three visible training pairs. Before implementation it failed with `NotImplementedError`, confirming the test exercised the missing solver. After implementation it passed all visible pairs. I then used the packet's visible-only checker.

**Remaining uncertainty.** The demonstrations do not show grids too small for the stated offsets, non-corner foreground cells, or a background other than the dominant color. The two queries remain within the demonstrated size and corner-marker regime.
