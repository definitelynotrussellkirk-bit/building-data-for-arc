# Solve work log

## Exposure declaration before solving

I had not seen task `c1b80aa665e4`, its Racket rule, generator, reference
solution, private labels, or prior solution notes before this visible-only solve.
I used only `solve-blind/challenge.json`, the rendered examples, and local Python
tests written in this directory.

## Revision 1 — isolated-cell hypothesis

Across all three training pairs, every nonzero cell belonging to a multi-cell
orthogonally connected same-color component is unchanged. Every nonzero cell
with no same-color orthogonal neighbor changes to color 9. This explains:

- the vertical color-4 pair in example 0 remaining color 4 while three singletons
  become 9;
- the three larger color-7 components in example 1 remaining color 7 while four
  isolated color-7 cells become 9; and
- the horizontal color-7 pair in example 2 remaining color 7 while the other
  three cells become 9.

I chose four-connectivity rather than diagonal connectivity. Query 0 contains a
color-3 cell at `(1, 12)` diagonally adjacent to the larger color-3 component,
which appears to be the intended discriminator; under this hypothesis that cell
is still a singleton and should become 9.

Before implementation I added `test_solution.py`, covering all visible training
pairs and a two-pixel diagonal probe. Running
`python3 -m unittest -v test_solution.py` failed in the expected way because the
stub had no implementation. I then implemented the minimal rule: copy the grid,
and recolor a nonzero cell to 9 exactly when none of its four orthogonal neighbors
has the same color.

Remaining uncertainty: the examples do not distinguish monochromatic components
from connectivity across touching different colors. No visible query contains
orthogonally touching different colors, so this does not affect the submitted
queries. The monochromatic interpretation is the simpler object rule supported
by the examples.
