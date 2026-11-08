# Blind solve notes — a2e8d5ad83e5

## Observations

- Each input contains one or more solid nonzero square components amid isolated
  distractor cells.
- In train 2, the 3×3 color-5 square extends its center row across the grid and
  its center column down the grid. Unreached distractors remain unchanged, while
  cells on an extended axis are overwritten by the square color.
- Train 0 has two 3×3 color-1 squares. Their two horizontal center axes and two
  vertical center axes are all present in the output. Because their colors agree,
  their overlaps remain color 1.
- Train 1 has color-4 and color-1 squares sharing the same center row. Their
  horizontal emissions overlap in different colors, and that whole row becomes
  background. Their vertical emissions remain except at the conflicting row.
- Test 0 includes a 4×4 square and a 2×2 square, suggesting that an even-sided
  square uses both central rows and both central columns.

## Hypothesis

Find every 4-connected, solid, axis-aligned nonzero square of side at least 2.
It emits its color along its middle row(s) and middle column(s), extending to the
full grid. Odd sides have one middle row/column; even sides have two. A cell hit
by one color becomes that color, a cell hit by multiple distinct colors becomes
background 0, and a cell hit by no emitter keeps its input value.

## Probe

I implemented the hypothesis independently against the three visible examples.
It reproduced all three outputs exactly (zero mismatched cells), including the
same-row cancellation in train 1. I therefore kept this as the first submitted
solve revision rather than manufacturing an additional failed attempt.

## Limitations considered

- I identify whole-color 4-connected components, so a square touching another
  same-color shape would merge and no longer qualify. The visible construction
  keeps the square objects separated from same-color distractors.
- The examples establish cancellation between different emitted colors and
  agreement between same-colored emitters; they do not show three-way overlap,
  for which I apply the same distinct-color rule.
