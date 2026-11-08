# Solve notes

## Visible pattern

Each training input contains two structures on background 0:

1. a large pattern made from repeated solid square blocks in one dominant color;
2. a compact dense 3×3 or 4×4 colored square.

The compact square is the palette/output template. Its dimensions define how
many logical blocks to read from the large pattern. At coordinate `(r, c)`, the
output copies the compact square's color when the corresponding large block is
present, otherwise it writes 0.

## Hypotheses considered

- **Copy/crop the compact square:** rejected because training outputs zero some
  palette cells.
- **Use palette color equality or a fixed checkerboard:** rejected because the
  kept positions change with the large block arrangement.
- **Use the largest connected component only:** rejected because disconnected
  same-color blocks all contribute.
- **Suppress the dominant color in output:** rejected directly by visible
  examples where a palette entry equals the dominant shape color and is copied.

## Implementation probe

Identify the uniquely frequent nonzero color as the block-pattern color. Find
its bounding box. Find the bounding box of all other nonzero colors; this locates
the dense palette even when one palette cell itself equals the dominant color.
Divide the large bounding-box dimensions by the palette dimensions and sample
the top-left cell of each logical block. Mask the palette position-for-position.

The shape-color palette cell can enlarge the shape-color bounding box. Integer
block-size inference remains stable on the visible examples, so the solver uses
the demonstrated quotient construction rather than trying to remove palette
cells by spatial heuristics.
