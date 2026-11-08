# Blind solve notes — 93ca517eac25

## Visible observations

- Every output preserves the grid and recolors exactly one 4-connected blue (`1`) object red (`2`).
- Each example also contains two non-blue clue components with distinct colors and shapes.
- The selected blue object's *tight bounding-box complement* is tiled by copies of one clue's **oriented** shape:
  - example 1: the red T pentomino has two vertical-domino gaps; the vertical domino is a clue;
  - example 2: the red L tetromino has one vertical-domino gap;
  - example 3: the red H-like heptomino has two singleton gaps.
- Rotation cannot be ignored: in example 1 the unselected 5-cell zigzag has horizontal-domino gaps while the selected T has vertical-domino gaps.
- In all three visible examples the applicable key is the lower-numbered clue color. This may be a deliberate ordering convention, but it is the weakest part of the inference because ARC color IDs are often categorical.

## Selection hypothesis implemented

1. Extract blue components and non-blue clue components using 4-connectivity.
2. Consider clues in ascending color order, preserving clue orientation.
3. A blue candidate matches a clue when every missing component in its tight bounding box is exactly that clue shape.
4. Prefer more repeated matching gaps; then prefer gaps carved along the bounding-box boundary rather than through its interior; then use distance to the clue and object size as deterministic tie-breakers.
5. Recolor only the best candidate red.

This explains the otherwise ambiguous second training example: both the 4-cell L and 7-cell U have a vertical-domino complement, but the U's complement includes an interior cell while the L's entire complement lies on its boundary.

## Alternatives considered and rejected

- Nearest object to either clue: contradicted by example 3.
- Selecting by blue-object area equal to a clue color: fits examples 1 or 2 separately but not example 3.
- Symmetry alone: the selected L in example 2 is asymmetric.
- Treating dominoes up to rotation: fails to distinguish the T from the zigzag in example 1.
- Matching the colored-plus-blue connected component directly: the examples vary between detached, singly attached, and multiply attached clues.

## Test expectations / uncertainty

- Test 1 has a singleton lower-color clue; the hypothesis selects the 6-cell blue shape with three singleton gaps rather than the 3-cell L with one gap.
- Test 2's lower-color clue is an L triomino, for which no blue tight-box complement matches. The solver therefore tries the other clue (a vertical domino), selecting the closest matching L tetromino. This fallback is substantially less certain than the training-supported cases.
