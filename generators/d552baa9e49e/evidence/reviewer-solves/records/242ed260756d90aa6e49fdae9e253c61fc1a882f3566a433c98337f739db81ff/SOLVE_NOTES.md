# Blind solve notes — d552baa9e49e

## Revision 1

The isolated colored cell at `(0, 0)` is metadata; the distant multicolor
pattern is the payload.  Removing the marker and taking the tight bounding box
exactly explains the output sizes while retaining zeros inside the box.

Observed transformations:

- marker `1`: the first payload is rotated 90 degrees clockwise;
- marker `2`: the second payload is rotated 180 degrees;
- marker `3`: the third payload is transposed across its main diagonal.

The visible examples do not directly demonstrate marker `4`, which occurs only
in a query.  I infer a compact two-pair code: odd markers use an axis swap and
even markers use a left/right reversal; markers 1–2 additionally reverse the
row direction.  Under that interpretation marker `4` is a horizontal mirror.
This is the main unresolved ambiguity; identity, vertical reflection, and the
other diagonal reflection cannot be ruled out from visible pairs alone.

The implementation deliberately uses no task-specific dimensions, colors, or
coordinates beyond recognizing the isolated upper-left marker and cropping the
remaining nonzero payload.
