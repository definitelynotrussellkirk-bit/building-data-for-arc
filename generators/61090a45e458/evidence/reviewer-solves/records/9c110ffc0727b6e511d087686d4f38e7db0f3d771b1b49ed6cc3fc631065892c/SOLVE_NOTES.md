# Solve work log

## Exposure declaration

I had already inspected and repaired this task's generator and semantic contract before this required post-repair solve, so earlier rule exposure is **yes**. During this solve I did not consult the Racket rule, generator source, reference solutions, private query labels, or earlier solution explanations; I used only the visible examples in `solve/README.md` and checker feedback.

## Revision 1 — frame-local singleton recoloring

**Observation.** Every visible scene contains one or more monochrome rectangular outlines. Inside each rectangle are exactly two nonzero colors: one occurs once and the other occupies a larger shape. In every training output, the larger shape is recolored to the singleton color while the rectangle, singleton, background, shape, and dimensions remain fixed.

Examples support processing rectangles independently. In training example 0, the left frame changes the four 7 cells to singleton color 6 while the right frame changes the four 5 cells to singleton color 9. Training example 2 shows vertically separated frames and target objects away from a single fixed corner, so a global-color or fixed-position rule is weaker than the frame-local count rule.

**Predicted queries.** Query 0 should change the four 6 cells inside the 7 frame to singleton color 4. Query 1 should change the four 7 cells inside the 2 frame to singleton color 9.

**Implementation.** Find 4-connected monochrome components that are exact rectangular perimeters. For each frame, count nonzero interior colors, identify the unique singleton and unique multi-cell color, and replace only the latter with the singleton color. This avoids relying on absolute location, frame orientation, or global color counts.

**Remaining uncertainty.** The visible examples consistently contain exactly one singleton and one larger object per frame. The implementation conservatively leaves a malformed or ambiguous frame unchanged rather than guessing.
