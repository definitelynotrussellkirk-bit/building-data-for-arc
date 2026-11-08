# Solve work log

## Earlier exposure

Before this solve episode I had already inspected the assigned generator and the canonical rule as part of the required generator review. This is therefore **not a blind solve**. After `solve_episode.py prepare`, I did not reopen the generator, Racket rule, reference solution, canonical labels, or private query labels; I used only `solve/challenge.json`, this work log, my Python solution, and visible checker feedback.

## Revision 1

**Visible pattern.** Every example contains two separate hollow orange (`7`) rectangular frames. Each frame behaves independently. Red (`2`) cells lie on the frame's left inner column and select rows. Green (`3`) cells lie on its top inner row and select columns. A different interior color is the frame-local fill key.

**Hypothesis.** For each frame, copy the input and replace every Cartesian-product intersection of its selected rows and selected columns with that frame's key color. Preserve the frame, all markers not at an intersection, the key cell, background, and other frames.

**Evidence/probes from the visible pairs.**

- A frame with two selected rows and three selected columns gains six fill-colored intersections.
- Intersections can overwrite an existing red or green marker at the shared inner axes, so the operation is not restricted to empty cells.
- Different frames in the same grid use different key colors, ruling out one global fill color.
- Key positions vary in the generated examples, so the key must be found by color/content rather than by a fixed coordinate.

**Implementation.** Find 4-connected components of color `7`, use each component's bounding rectangle as one frame, read row/column markers from the two inner axes, choose the most frequent interior color outside `{0,2,3,7}` as the local key, and paint the Cartesian product in a copied grid.

**Alternatives rejected.** Filling the whole interior, transforming only the first frame, using one global key, or using a fixed bottom-right key all contradict visible examples.

**Remaining uncertainty.** The visible examples provide one key color per frame. The solution uses most-frequency with row-major first-seen tie behavior if multiple candidate colors appear, which is a conservative generalization.
