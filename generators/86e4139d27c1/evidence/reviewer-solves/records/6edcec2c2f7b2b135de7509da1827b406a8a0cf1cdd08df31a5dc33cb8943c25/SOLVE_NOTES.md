# Visible-only solve: 86e4139d27c1

Earlier rule exposure: no. Reference consulted during solve: no.
Only the public preparation output and visible challenge were inspected.

## Observations and first hypothesis

The three demonstrations preserve grid dimensions: 11 by 12, 16 by 15,
and 10 by 13. Each has exactly two blue (1) markers. The output paints a
five-cell green (3) plus at their midpoint and otherwise preserves the input.
The marker coordinates and inferred centers are (0,8)/(4,8) -> (2,8),
(11,11)/(11,13) -> (11,12), and (8,1)/(8,7) -> (8,4).
The second demonstration overwrites both blue markers, so the plus overwrites
occupied cells as well as background; it does not preserve markers specially.

Revision 1 implements this rule without using generator code or labels.
One query has diagonally separated markers and a half-integer row midpoint.
The visible demonstrations do not distinguish floor from ceil at half-integers.
I choose integer floor independently for each coordinate, recording this
generalization as uncertain rather than claiming the examples prove it.
Clipping the plus at the boundary is likewise a natural untested extension.

No earlier failed implementation or artificial negative was created. The
official visible checker will determine agreement on the three demonstrations;
masked query correctness remains unknown and reserved for maintainer scoring.
