# Blind solve notes — task `1a5d49e539de`

I used only the visible examples in `solve-blind/challenge.json` / `README.md`.

## Observations

- Each input contains four spatially separated foreground figures when diagonal contact counts as connected (8-connectivity).
- The required output is exactly one cropped figure; no recoloring or geometric transformation is applied.
- In every training example, three figures are mirror-symmetric across a vertical axis (each row reads the same left-to-right and right-to-left).
- The output figure is the unique figure that is **not** left-right mirror symmetric.
- This rule picks the lower-right figure in query 0 and the upper-left figure in query 1.

## Implementation

Find monochromatic 8-connected components, crop each to its bounding box, compare the crop with its row-wise reversal, and return the unique mismatch. I added an explicit uniqueness check rather than silently selecting the first candidate.

No generator, canonical rule, reference solution, private label, or earlier solve explanation was consulted.
