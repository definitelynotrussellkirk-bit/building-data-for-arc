# Blind solve notes

## Observations

- Each input has three non-background colour swatches at upper left and three
  shapes drawn in colour 5 at upper right.  Their left-to-right orders align.
- A dense rectangular matrix of the three swatch colours appears below a blank
  separator.
- Output dimensions equal `(matrix rows × glyph height)` by
  `(matrix columns × glyph width)`.
- Splitting each training output into those blocks shows that a matrix cell of
  colour `c` becomes the corresponding colour-5 glyph mask, repainted with `c`.

## Hypothesis implemented

Parse the ordered swatches, parse the three colour-5 glyph slots, locate the
lower colour matrix, then tile the mapped glyph for each matrix entry.  Empty
pixels remain background 0.

## Parsing choices and limits

- Colour 5 is treated as the template ink because it is the only colour shared
  by all upper-right glyphs and absent from the lower matrices in every visible
  example.
- Glyph columns are separated by blank columns.  The visible tasks paint every
  glyph's top edge, so an internal blank column cannot accidentally split a
  glyph slot.
- Legend swatches can be one or more repeated cells; consecutive duplicates are
  collapsed.
- The lower matrix is the bounding rectangle of all nonzero cells below the
  glyph bank and is required to contain only keyed colours.
