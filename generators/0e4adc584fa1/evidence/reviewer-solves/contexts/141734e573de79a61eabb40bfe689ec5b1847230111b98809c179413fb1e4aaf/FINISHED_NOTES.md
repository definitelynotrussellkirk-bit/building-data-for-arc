# Visible-only solve work log

I used only `solve/challenge.json` during this solve. I had earlier exposure to the repaired task while reviewing it, so this is not a blind inference record; the final declaration will say `earlier-exposure yes`. I did not consult the generator, Racket rule, reference outputs, or private query labels after preparation.

## Hypothesis

Each input contains a multi-cell foreground object and one orthogonally isolated single cell whose color is in 1–4. The output removes the isolated cell, crops the remaining object to its nonzero bounding box, then rotates the crop according to the isolated cell's color.

The four visible demonstrations expose the complete table:

- marker 1: identity;
- marker 2: 90 degrees clockwise;
- marker 3: 180 degrees;
- marker 4: 90 degrees counterclockwise.

I verified the table cell-by-cell against each visible output. The first query has marker 4 and the second has marker 1. I will implement the general procedure rather than hard-code those cases. For robustness, if more than one isolated 1–4 cell appears, I remove all such controls and use the last one in row-major order; that convention is not needed by the visible episode but is consistent with the observable pattern.
