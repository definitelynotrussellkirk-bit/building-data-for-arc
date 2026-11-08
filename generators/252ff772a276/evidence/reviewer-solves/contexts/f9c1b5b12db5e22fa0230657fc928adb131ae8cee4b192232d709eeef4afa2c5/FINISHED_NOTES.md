# Blind solve notes — 252ff772a276

Visible examples contain several color-1 rectangular frames. The output is one cropped frame: its color-2 markers are preserved and every remaining zero in its interior becomes color 3.

Hypothesis: choose the frame containing the greatest number of color-2 markers. Train 0 and 1 choose the three-marker frame over the one-marker frame. Train 2 has two three-marker frames and selects the earlier/topmost one, so I use row-major top-left position as the tie break. This count rule is simpler and better supported than marker density: train 2 would also favor the first by density, but the second query visibly supplies 1-, 2-, and 3-marker frames and therefore distinguishes the count rule.

Implementation: find 4-connected color-1 components whose cells are exactly a rectangular perimeter, count interior 2s, choose maximum count with top-left tie-breaking, crop it, and recolor only interior zeros to 3. Small non-rectangular color-1 noise is ignored.
