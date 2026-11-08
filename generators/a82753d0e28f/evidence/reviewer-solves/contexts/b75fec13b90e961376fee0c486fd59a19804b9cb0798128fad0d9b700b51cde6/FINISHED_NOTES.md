# Solve work log

## Prior exposure

I had already inspected and repaired this task's generator before this required post-repair solve, so earlier rule exposure is **yes**. During the solve episode I did not reopen the generator, canonical rule, reference solution, private labels, or previous solution explanations; I used only the visible examples in `solve/README.md`.

## Revision 1

**Observation.** Every nonzero input cell remains colored and produces same-color marks at offsets `(±1, ±2)` and `(±2, ±1)`, exactly the eight chess-knight destinations clipped to the grid. Output shape equals input shape and all other cells are zero.

**Collision probe from visible example 0.** The color-5 seed at `(2,3)` and color-3 seed at `(2,7)` both reach `(1,5)` and `(3,5)`. The visible output uses color 3 at both cells. Since `(2,7)` is later in row-major order, the examples support sequential row-major painting with later seeds overwriting earlier paint, rather than max color, min color, or first-writer precedence.

**Implementation.** Start from an all-zero grid. Scan the input row by row and column by column. For each nonzero seed, write its color at the seed and each in-bounds knight destination. Direct assignment naturally gives later seeds precedence.

**Remaining uncertainty.** The finite examples cannot rule out every contrived equivalent rule, but they directly exercise clipping, multiple seeds, repeated colors, and an unequal-color halo collision. No additional revision appeared justified before visible-example checking.
