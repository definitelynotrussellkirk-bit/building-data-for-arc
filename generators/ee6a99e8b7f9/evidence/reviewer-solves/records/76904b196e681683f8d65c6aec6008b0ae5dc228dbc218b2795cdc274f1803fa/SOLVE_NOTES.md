# Exposed post-repair solve notes

Earlier exposure: yes. I reviewed this generator before this solve, so this is not
blind. During the solve I used only the visible examples and did not consult the
Racket rule, generator source, private labels, reference solutions, or earlier
solution code.

## Visible-example hypothesis

- Background is literal color 8.
- Each same-color 4-connected color-5 or color-6 region is a filled rectangle.
- A color-9 source immediately outside a rectangle edge belongs to that rectangle.
- For a gray (5) rectangle: erase the rectangle, keep the exterior source dot,
  and place a 9 on the adjacent cell of the rectangle's old edge.
- For a pink (6) rectangle: retain the rectangle, clear the exterior source dot,
  and place a 9 on its center row or center column, preserving the coordinate
  parallel to the approached edge.
- Even dimensions in train examples 2 and 3 show floor/lower-index tie-breaking:
  center index is `(lo + hi) // 2`.
- Apply every dot independently; multiple destinations may coexist or collide.

I implemented component extraction and geometric dot ownership directly from
this hypothesis. The four visible examples should exercise single pink, mixed
pink/gray, non-3x3/even rectangles, multiple dots, and border-touching shapes.
