# 22d91d7a09d2

COLOR-7 (orange) background square grid (size ∈ 7-10) with: ONE 5×5 MARKER CONTEXT PATCH pasted at a random interior position (r0, c0 ∈ 1..size-6) — drawn from _PATCHES bank (3 variants of 5×5 patches: all-orange-7 with ONE color-4 center marker at (2,2); same with color-6 center; or color-9 at (2,2) + color-1 at (2,4) + scattered color-9s in bottom-right corner). All patches are fully in-bounds; color-7 dominates the patch and the rest of the grid. Rule (RECOGNIZE THE 5×5 MARKER CONTEXT; APPLY A CANONICAL RADIUS-2 RECOLOR TABLE TO RECOLOR THE CENTER MARKER OR ADD A SPECIFIC DECORATION BASED ON THE PATTERN OF NON-7 CELLS WITHIN RADIUS 2 OF THE CENTER): LOCATE the patch by scanning for the 5×5 marker context. READ the non-7 cells in the Chebyshev-distance-2 window around the center. APPLY a fixed recolor table that maps the surrounding pattern to a new center color (or paints additional cells). Net: marker context decodes via a fixed local lookup table; the result is a context-dependent recolor.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
