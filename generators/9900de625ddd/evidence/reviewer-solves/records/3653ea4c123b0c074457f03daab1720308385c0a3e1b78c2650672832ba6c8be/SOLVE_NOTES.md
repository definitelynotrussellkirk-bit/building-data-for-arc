# Solve work log

## Exposure declaration before solving

I had not opened task `9900de625ddd`'s generator, Racket rule, notes, reference
solutions, private labels, or prior audit material. I saw only the packet-level
instructions and `solve-blind/challenge.json`.

## Revision 1 — one-cell erosion of every coloured region

The visible outputs retain only cells whose entire 3×3 neighbourhood has the
same nonzero colour. Equivalently, each coloured shape is eroded by one cell in
all eight directions, with the grid exterior acting as background.

Evidence from the demonstrations:

- Every solid 3×3 square becomes its single centre cell.
- A solid 4×4 rectangle becomes its central 2×2 rectangle.
- A solid 5×5 square becomes its central 3×3 square.
- A 4×4 colour-3 block missing its lower-left corner loses the otherwise-inner
  cell adjacent to that defect, while retaining the three inner cells whose
  3×3 neighbourhoods remain intact.
- A 3×3 block containing one differently coloured border cell produces no
  survivor because its centre no longer has a uniform 3×3 neighbourhood.
- A 2×2 block vanishes because no cell can have a full same-colour 3×3
  neighbourhood.

I implemented this directly: initialize an all-zero output and copy a nonzero
cell only when all nine cells centred on it are in bounds and equal to it.
This also predicts the two test grids without special-casing components:
(1) one interior orange cell and one interior green cell survive; (2) the
centres of the two solid 3×3 squares survive.

Remaining uncertainty is low. A component-wise erosion and this local predicate
are equivalent for these grids, including touching differently coloured cells.
