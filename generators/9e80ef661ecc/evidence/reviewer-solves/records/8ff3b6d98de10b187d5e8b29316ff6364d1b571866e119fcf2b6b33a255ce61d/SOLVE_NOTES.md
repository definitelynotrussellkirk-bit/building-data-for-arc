# Solve notes

## Visible-example hypothesis

The transformation keeps every foreground object's occupied cells fixed and
changes only its color. Objects are orthogonally connected cells of the same
input color, not all touching nonzero cells:

- Train 3 has differently colored objects touching at an edge, yet they receive
  different output colors.
- Train 2 has several disconnected objects with the same input color, yet they
  receive different output colors.

The output color depends on the number of **connected enclosed regions** in the
object's own bounding-box complement, rather than foreground area, input color,
or the number of enclosed cells. Train 1's 4×4 ring encloses four cells but one
connected hole and becomes 3.

Observed mapping across the four demonstrations:

- 0 holes → 2
- 1 hole → 3
- 2 holes → 4
- 3 holes → 6
- 4 holes → 9

I therefore extract same-color 4-connected components, count complement regions
inside each component bounding box that cannot reach the box boundary, and
recolor that component by the table above. Unknown larger counts use 9, matching
the demonstrated 4-hole branch's terminal category.

## Test-input expectations before execution

Test 1 contains a one-hole 4×4 ring, a solid 2×2 object, and a two-hole 3×5
object, so they should become 3, 2, and 4 respectively.

Test 2 contains three disconnected same-colored 3×5 objects engineered to have
one, two, and zero holes despite equal area/bounding boxes, so they should become
3, 4, and 2 independently.
