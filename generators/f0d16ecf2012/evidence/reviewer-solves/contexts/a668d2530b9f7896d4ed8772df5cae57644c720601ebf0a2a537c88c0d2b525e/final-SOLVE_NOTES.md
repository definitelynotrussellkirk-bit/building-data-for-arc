# Fresh visible-only solve notes — round 2

This is a **human work log**, not a token-level model trace.

## Exposure declaration

Earlier rule exposure: **yes**. I reviewed this generator and its rule before
starting the required solve phase. During this solve phase I opened only
`solve/challenge.json`; I did not consult the generator, Racket source,
reference solution, private labels, or the archived first-round solve.

## Visible evidence and hypothesis

The color-9 rows and side columns are unchanged in every demonstration, so I
treat them as fixed walls. Every other nonzero color forms one or more
4-connected components. Connected rectangles and L-like shapes retain their
relative offsets while moving east. Diagonally touching cells do not remain a
diagonal: they become separate cells in the rightmost interior column, which
indicates that diagonal contact is not connectivity and each 4-connected
component moves independently.

Primary hypothesis: extract same-color 4-connected non-wall components, then
translate each rigidly east until another east step would hit a 9-wall or the
grid boundary. Other colored components do not block that motion.

Alternatives rejected from the visible pairs:

- moving every colored cell independently would destroy the L and rectangle;
- moving each occupied row independently would distort ragged connected shapes;
- treating all same-color cells in one lane as a single object would preserve
  the diagonal rather than producing a vertical stack;
- moving one step is contradicted by the large displacements.

## Revision 0001

Implemented BFS same-color 4-connectivity, preserved walls, and moved each
component east on a walls-only board until blocked. This is the first and only
revision unless visible-example feedback identifies a mismatch.
