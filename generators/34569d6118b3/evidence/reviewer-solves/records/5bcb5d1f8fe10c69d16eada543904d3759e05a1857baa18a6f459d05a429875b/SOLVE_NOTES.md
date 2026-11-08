# Solve work log

## Exposure declaration before solving

I had not opened task `34569d6118b3`'s generator, rule, notes, reference
solutions, private labels, or prior solve explanations. I had only read the
packet-level instructions and `solve-blind/challenge.json`.

## Revision 1 — keyed stamp substitution

**Observation.** Every visible input has three regions: a top-row list of
nonzero key colors, a row-aligned collection of shapes drawn with color 5, and
a lower rectangular grid containing the key colors. A fully zero row separates
the upper legend from the lower grid. The output dimensions equal lower-grid
height × stamp height and lower-grid width × stamp width.

**Hypothesis.** Read the key colors from left to right. Match them to the
left-to-right runs of 5 on the top row. Each run identifies the width and column
range of one binary stamp; the rows above the first blank separator give its
height. Replace each lower-grid cell by its corresponding stamp, recoloring each
5 to the cell's key color and leaving stamp zeros as zero.

**Probes.** I manually decomposed all three training pairs. In the first pair,
the lower row `[1,3,3,1]` becomes four adjacent 3×3 stamps, agreeing exactly
with output rows 0–2. The second pair gives 5×3 stamps and the third gives 3×5
stamps, which explains their 20×12 and 12×20 outputs without changing the rule.
The repeated key runs in the first test are treated as one key run apiece.

**Implementation choices.** The program finds the first blank row, infers the
stamp marker as the most frequent nonzero upper value, uses contiguous marker
runs on row 0 as stamp bounds, uses contiguous non-marker runs before the first
stamp as keys, and crops the lower grid to its nonzero bounding box. Internal
zeros in that crop are preserved as blank output blocks.

**Alternatives rejected.** This is not a simple enlargement of the lower grid:
different colors select different shapes. It is also not a fixed 3×3 tiling,
since the visible examples use 5×3 and 3×5 stamps.

**Remaining uncertainty.** The visible format consistently places a solid
marker run across the top row of every stamp and uses a fully blank separator
row. The implementation relies on those layout cues.
