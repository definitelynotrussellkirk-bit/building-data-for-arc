# Solve notes

This is a human work log based only on the visible examples prepared in this solve episode. I had earlier exposure to the selected task's rule during generator review, so this is not a blind solve. I did not reopen the generator, Racket source, canonical answers, or private labels after preparation.

## Hypothesis

The color-6 cells form separate rectangular objects. Some are solid filled rectangles and some are hollow rectangle borders. Across all three demonstrations, only the zero-valued cells strictly inside a hollow color-6 border change, becoming color 8. Solid color-6 rectangles and the short non-6 decoration stay unchanged. When two hollow frames are present, both are transformed, so the operation is applied independently to every qualifying component.

## Implementation probe

I implemented four-connected component extraction for color 6. For each component I compute its bounding box and compare the exact component cell set with that box's border. A matching border of at least 3 by 3 has its strict interior painted 8 in a copied grid; all other components are preserved.

## Alternatives rejected from the examples

- Filling every color-6 bounding box would modify the already-solid rectangles, contrary to every demonstration.
- Filling only one frame would fail train examples 0 and 2, each of which transforms two hollow frames.
- Treating every rectangle-like group as one object without connected components would risk merging spatially separate objects that share color 6.
