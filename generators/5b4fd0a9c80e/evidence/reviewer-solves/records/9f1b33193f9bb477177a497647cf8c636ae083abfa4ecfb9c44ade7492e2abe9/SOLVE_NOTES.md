# Solve work log

I had earlier exposure to the selected task's rule while reviewing the generator, so this is not an independent discovery claim. During this solve I did not reopen the generator, Racket authority, canonical ledger, private labels, counterexample, reference probe, or earlier solution notes; I used only `challenge.json`, the visible examples, and my own implementation.

## Hypothesis from the visible examples

Each nonzero, same-color, 4-connected component is handled independently. The component's exact bounding-box crop is preserved, including zeros inside that box. Crops are sorted by `(number of colored cells, source top row, source left column)`, then stacked vertically with one all-zero separator row. Every crop is floor-centered in an output whose width is the widest crop.

Visible evidence for the tie-break is present in the three training examples: example 0 orders the two area-4 objects by top row, and example 2 orders the two area-5 objects by left column when their top rows tie. The different crop widths also expose floor-centering rather than arbitrary source alignment.

## Implementation and checks

I implemented a direct 4-neighbor flood fill, raw bounding-box extraction, the observed sort key, one-row separators, and integer floor-centering. No task or rule implementation is imported. I then compared `solve` against all three visible training outputs before invoking the official visible-only check.

Remaining uncertainty before the check: whether connectivity was intended across colors or diagonally. The demonstrations use distinct colors and orthogonal shapes; same-color 4-connectivity is the simplest rule consistent with standard ARC object extraction and all visible pairs.
