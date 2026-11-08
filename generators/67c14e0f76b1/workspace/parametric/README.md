# Native parametric family: 67c14e0f76b1

- `mark_only` is the exact canonical program: change each zero with immediate
  blue neighbors on its left and right to red (2).
- `largest_marked` applies that exact rule first, finds the unique largest
  four-connected component consisting of newly marked red cells, and recolors
  that component to azure (8).

The inputs contain three vertical stacks of horizontal gaps with distinct
lengths.  Stage B cannot choose the winner before Stage A because the target
cells are still background.  The retained wrong-order program instead chooses
and recolors the largest raw blue component before marking, which destroys one
side of the corresponding gaps and changes the final output.

Both settings use identical input grids. Generation supports 2–6
representations and 1–4 private queries with stable, independent prefixes;
the fourth query is a substantive 30x30 boundary case.
