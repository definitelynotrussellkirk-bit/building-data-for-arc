# Solve notes

## Visible observations

- Every input and output preserves a regular lattice of one-pixel divider rows and columns around uniform 2x2 cells.
- The divider is the modal non-zero color and changes between examples, so its numeric value is not the semantic rule.
- A marker color occurring at two or more coarse cells in one coarse row is extended across every intervening coarse cell.
- The same operation applies vertically.
- A three-marker L shape therefore produces both a horizontal and a vertical arm; isolated or off-line markers remain unchanged.
- With three collinear markers, the visible example fills the complete interval from the outermost first marker to the outermost last marker, not merely one adjacent pair.

## Hypothesis implemented

Infer the modal non-zero divider color, read all non-divider non-zero uniform 2x2 coarse cells as colored markers, then process each color independently. For every coarse row and column containing at least two markers of that color, paint the inclusive min-to-max interval. Preserve all other cells and all divider pixels.

This is an exposed post-repair solve: I had already inspected the generator rule while repairing it. I did not consult a reference implementation or hidden query labels during this solve episode.
