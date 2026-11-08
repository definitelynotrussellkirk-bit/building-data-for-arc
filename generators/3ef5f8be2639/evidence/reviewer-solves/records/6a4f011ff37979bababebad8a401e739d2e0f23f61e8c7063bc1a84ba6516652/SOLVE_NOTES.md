# Solve work log

## Exposure

Before this solve I read only the packet-wide start/duties material and the visible
examples printed by `python3 review.py blind prepare`. I did not open this task's
generator, canonical rule, labels, solutions, notes, catalog entry, or audit evidence.

## Revision 1 — rotated farthest red/green segment

Visible observations:

- Example 1's vertically separated red/green pair becomes a horizontal 3-cell
  azure segment through the same midpoint.
- Example 2's farthest red/green pair is diagonal across a 2x2 box. Rotating the
  segment 90 degrees gives the other diagonal; filling its axis-aligned box gives
  the demonstrated 2x2 azure square.
- Example 0 has a one-cell vertical red/green pair tied in distance with a
  horizontal pair. A 90-degree rotation lands on half-cell endpoints; outward
  floor/ceil rounding gives exactly the demonstrated 2x3 azure rectangle.

Implementation: choose the farthest cross-color pair by squared Euclidean distance,
prefer greater vertical displacement on a tie (the only visible tie), rotate its
endpoints 90 degrees around their midpoint using exact half-integer arithmetic, and
fill the outward-rounded bounding box with 8 on an otherwise zero grid.

Predicted query behavior:

- Query 0 becomes a vertical 3-cell segment centered between the horizontal pair.
- Query 1 uses the farther diagonal red/green pair and becomes a 2x2 azure box.

Remaining uncertainty: the examples do not prove the pair-selection tie policy, or
whether all same-color markers encode the same geometry rather than acting as pair
selection cues. The two queries do not appear to depend on the visible tie.
