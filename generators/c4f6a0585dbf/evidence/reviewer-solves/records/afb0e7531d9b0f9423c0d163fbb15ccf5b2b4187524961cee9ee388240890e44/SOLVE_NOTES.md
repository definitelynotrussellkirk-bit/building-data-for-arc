# Blind solve notes — c4f6a0585dbf

## Visible observations

- Each input contains one dense rectangle made only of `1` and `4`; all other
  non-background cells are isolated/noisy `4`s.
- The `4`s inside that rectangle define a pattern.  Output preserves all input
  cells and turns selected `0`s into `1`s.
- Train 0 adds one 5×5 rectangle around a 90°-rotated copy of the three-`4`
  exemplar pattern.
- Train 1 explains the apparently enlarged shapes: the horizontal two-`4`
  exemplar matches both its 0° and 180° placements at different origins, while
  the vertical target matches both 90° and 270° placements.  The union is a
  5×4 or 4×5 block.
- Train 2 contains overlapping matches and matches clipped at the bottom/right
  grid edges.  An adjacent pair near the top-left is *not* boxed because its
  candidate window contains an extra `4`; therefore matching is exact within
  the visible stamp window, not merely subset matching.

## Hypothesis implemented

1. Use the bounding box of all `1`s as the exemplar rectangle.
2. Record the relative coordinates of its `4`s.
3. Generate the four unique rotations of the rectangle and pattern.
4. For every possible origin, including origins whose margin is clipped by a
   grid edge, require every pattern `4` to be visible and present and require
   there to be no other `4` in the visible rectangle.
5. Fill every matching rectangle's `0`s with `1`, preserving all `4`s and the
   original exemplar.  Matches are determined from the original input so their
   added `1`s cannot create or suppress later matches.

## Alternatives and uncertainty

- Reflections would also fit these visible examples, but no reflected target is
  demonstrated.  I retained rotations only because every positive example is
  explained by rotation and adding reflection would assert an unsupported
  symmetry.
- The exemplar bounds are inferred from the `1`s.  This assumes its outer rows
  and columns each retain at least one `1`, as all visible examples do.
