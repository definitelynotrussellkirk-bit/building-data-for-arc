# Solve work log

## Exposure declaration before solving

I had already reviewed this task's generator and canonical rule during the repair phase, so this is **not blind** and `earlier-exposure` must be `yes`.  During this solve phase I did not reopen the generator, Racket source, canonical labels, private query labels, prior solution explanations, or repair notes.  I used only the public presentation produced by `solve prepare`, `solve/challenge.json`, my own Python, and visible-example feedback.

## Revision 1 — cross, center, and immediate diagonals

Visible pattern:

- Each original blue (`1`) input cell is a center.
- Its entire row and entire column become blue.
- The original center becomes red (`2`).
- Its four immediate diagonal neighbors become green (`3`) when in bounds.
- Only original input markers are centers; newly painted blue cells do not recurse.
- Markers are processed in the visible row-major order.  This detail is mostly latent in the examples but makes overlapping paint deterministic.

The boundary marker at `(10,0)` in train example 2 is useful: it has only the in-bounds diagonal `(9,1)`, confirming clipping rather than wrapping or padding.  Background color is preserved elsewhere and can be `7`, `8`, or `9`, so the transformation is marker-role based rather than tied to one background.

I implemented a shape-preserving copy, captured all original marker coordinates first, and applied the stamp sequentially.  A local comparison against the three public training outputs matched all cells, so I kept this as the first submitted revision.  Remaining uncertainty is only interaction precedence on marker layouts unlike the visible examples; the captured-marker, row-major implementation is the simplest rule consistent with all displayed evidence.
