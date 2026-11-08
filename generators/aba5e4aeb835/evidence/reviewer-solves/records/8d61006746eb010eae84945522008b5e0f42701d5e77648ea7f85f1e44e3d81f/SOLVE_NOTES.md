# Solve work log

Earlier exposure to this task's rule before the blind episode: **no**. I had
only read the packet-level instructions and the visible examples printed by
`solve_episode.py blind prepare`; I did not open this task's generator, Racket
rule, notes, solutions, private labels, or audit records.

## Revision 1 — boundary ray with two mirror orientations

All four training grids preserve every original nonzero cell and add only color
8. The unique red cell (2) lies on one boundary side. The added cells begin just
inside that red cell and form an orthogonal ray. Gray cells (5) are untouched and
appear to be absorbers/obstacles rather than waypoints.

The decisive probe was to trace the ray direction at each colored waypoint:

- In train 0, the left-edge red emits east; green turns east→north; yellow turns
  north→west; the ray exits the left edge.
- In train 1, the top-edge red emits south; yellow turns south→east; green turns
  east→north; the next yellow turns north→west and the immediately adjacent gray
  cell absorbs the ray.
- In train 2, the route is east→north→west→south→east→north through alternating
  green/yellow waypoints. This distinguishes mirror behavior from a rule that
  merely connects aligned markers.
- In train 3, four green cells cause west→south→west→south→west. This shows that
  green is a fixed slash mirror rather than a generic “turn left” instruction.

Thus green (3) behaves as `/`, mapping `(dr,dc)` to `(-dc,-dr)`, while yellow
(4) behaves as `\\`, mapping `(dr,dc)` to `(dc,dr)`. Empty traversed cells become
8, mirrors remain visible, gray terminates the ray, and leaving the grid ends it.
I added repeated-state detection as a defensive guard against a closed mirror
loop. The visible examples and both query sources are non-corner boundary cells;
corner-source direction remains outside the observed evidence.

Program: `solve-blind/solution.py`.
