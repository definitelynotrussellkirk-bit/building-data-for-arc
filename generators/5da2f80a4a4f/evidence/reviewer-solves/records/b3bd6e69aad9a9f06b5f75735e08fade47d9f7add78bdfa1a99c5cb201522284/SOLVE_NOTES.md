# Solve work log

Earlier exposure: none to task `5da2f80a4a4f`, its rule, generator, notes, or solutions. I used only `solve-blind/challenge.json`.

## Revision 1 — crop the frame and enlarge the motif

Observation: every input contains a rectangular border of color 2. The expected output is exactly that border's bounding rectangle, not the original canvas. Inside the border is a compact colored motif surrounded by zeros.

Across the three examples, the motif is enlarged by nearest-neighbor repetition until it fills the entire frame interior:

- Example 1: a 2×2 motif fills a 4×4 interior, so every motif cell becomes 2×2.
- Example 2: a 4×4 motif fills an 8×8 interior, again 2×2 repetition.
- Example 3: a 4×2 motif fills an 8×10 interior, so every cell becomes 2×5.

Implementation hypothesis: locate the color-2 frame by its bounding box; create an output of that size with a one-cell color-2 border; locate the bounding box of nonzero, non-frame cells inside; and map every output-interior coordinate to the corresponding motif coordinate by integer nearest-neighbor scaling. Zeros within the motif bounding box, if any, are preserved.

I chose coordinate mapping rather than assuming a fixed repeat factor so the program remains defined if an interior dimension is not an exact multiple of the motif dimension. Remaining uncertainty: the visible examples all use color 2 as the frame and a one-cell-thick rectangular border, so the solution intentionally follows that evidence.
