# Blind solve notes — 5e619caf1f27

I used only the visible examples in this solve.

## Observations

- Every input has one solid inner rectangle nested inside a rectangular frame of a second nonzero color.
- Every output preserves the original object and fills an additional rectangular layer with the inner color.
- The added layer is uniform on all sides before clipping to the grid.
- Measured layer widths in the four demonstrations are 3, 1, 2, and 2.

## Hypotheses considered

- Nearest-grid-edge padding: rejected because examples 0 and 2 have the same minimum padding (4) but different added widths (3 and 2).
- Maximum frame thickness: rejected because all four frames have maximum thickness 2 while the outputs vary.
- Inner rectangle minimum dimension: rejected by examples 1 and 3.
- Color lookup: it fits this one episode but is not color-invariant, so I avoided using it as the primary rule.

The demonstrations do not expose an obvious unique scalar encoding.  The smallest color-invariant expression I found that exactly matches all four widths is the maximum of:

1. outer rectangle aspect mismatch `|H-W|`,
2. inner rectangle aspect mismatch `|h-w|`, and
3. total opposite-side frame imbalance `|top-bottom| + |left-right|`.

This predicts width 2 for both queries.  Query 1 reaches past the top boundary, so the implementation clips the added rectangle to the grid.  I regard the scalar rule as uncertain but the structural transformation as high confidence.
