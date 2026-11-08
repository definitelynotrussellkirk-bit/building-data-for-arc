# Solve work log

Earlier rule exposure: **no**. I inspected only the visible challenge presentation and my own component-analysis script before writing this solution.

## Revision 1 — second-smallest object, doubled in place

Hypothesis: split color 3 into 4-connected objects, rank them by cell count, select the second-smallest object, replace every selected cell by a 2×2 block, preserve the selected object's bounding-box top-left, recolor to 8, and clear all other cells.

Evidence from the three visible examples:

- Example 0 component areas are 1, 3, 5, 6, 7. The area-3 vertical line is selected and becomes a 2×6 cyan rectangle at the same top-left.
- Example 1 areas are 2, 5, 6, 7, 8. The area-5 shape is selected; its output is exactly its 2× nearest-neighbor enlargement.
- Example 2 areas are 2, 4, 6, 7, 8. The area-4 shape is selected and doubled identically.

Alternatives considered and rejected: selecting the smallest object fails all examples; selecting by location or simple fit-within-canvas does not explain example 0 because another object also fits when doubled. The consistent discriminator is second-smallest area.

A local visible-example test was written first and failed on the original `NotImplementedError`. The implementation then reproduced all three visible outputs. Remaining uncertainty: the examples have distinct component areas, so tie behavior is unobserved; the code uses top-left order only as a deterministic fallback.
