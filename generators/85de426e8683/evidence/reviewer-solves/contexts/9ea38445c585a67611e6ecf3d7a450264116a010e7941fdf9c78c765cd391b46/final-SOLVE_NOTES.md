# Solve work log

This is a human work log. I had already seen the task's rule while reviewing the
generator, so this is **not blind**; I did not reopen the generator, Racket
source, canonical record, reference solution, or private labels during this
solve phase. The implementation below was checked against `challenge.json`
only.

## Revision 1

Visible-example hypothesis:

- Color 5 cells must first be grouped into whole 8-connected components.
- A component is selected only when it has exactly three cells and its
  normalized shape is one of the two 45-degree diagonals.
- The middle cell of each selected component changes from 5 to 4.
- Horizontal/vertical triples, longer or branched gray components, unrelated
  colors, and existing 4 cells remain unchanged.

Evidence from the four demonstrations:

- The first example shows both diagonal slopes and changes both centers.
- The second leaves a five-cell diagonal chain unchanged while changing the
  center of a separate three-cell diagonal, rejecting a local sliding-window
  interpretation.
- The third shows multiple selected components alongside a larger gray
  near-miss.
- The fourth preserves horizontal and vertical gray triples and a pre-existing
  yellow cell while changing only exact diagonal components.

Implementation probe: copy the grid, flood-fill color-5 cells using eight-neighbor
connectivity without crossing background, normalize each complete component,
and recolor the row-middle cell only for the two exact three-cell diagonal
shapes. No alternative revision was needed unless the visible-example checker
reported a mismatch.

Remaining uncertainty: private queries are hidden. The main possible ambiguity
would be whether connectivity were four-neighbor rather than eight-neighbor,
but the examples' diagonal objects necessarily imply diagonal connectivity and
the larger diagonal chains demonstrate whole-object scope.
