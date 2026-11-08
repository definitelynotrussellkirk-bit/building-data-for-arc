# Solve work log

## Prior exposure

This is not a blind solve. Before this episode I had inspected and repaired the
selected generator and had seen the intended task rule. During this solve
episode I did not reopen the generator, Racket authority, canonical data,
private labels, reference solutions, or earlier solution explanations. I used
only the visible examples printed by `solve_episode.py prepare` and the solve
scaffold.

## Revision 1

**Visible-example hypothesis.** Treat color 7 as the only candidate-object
color, split it into same-color 4-connected components, select the component
with the fewest cells, crop its bounding box, and replace its occupied cells
with color 8 while preserving background holes as 0. Ignore differently
colored objects even when they are smaller.

Evidence in the five demonstrations:

- Example 0 contains a one-cell color-5 decoy, but the output is the two-cell
  horizontal orange component, so the rule cannot be “smallest nonzero object.”
- The selected orange object changes location and orientation across examples:
  horizontal 2, bent 4, vertical 3, bent 5, and bent 6 cells.
- Every output has the selected object's tight dimensions and exact occupancy,
  recolored from 7 to 8.

**Implementation.** Enumerate orange components with cardinal adjacency,
choose the minimum by `(area, row-major first cell)` as a deterministic fallback,
and render its tight crop. The visible data indicate the minimum is unique, so
the fallback should not affect these examples.

**Expected queries before checking.** Query 0 should return the three-cell
horizontal orange object at the top right as `[[8, 8, 8]]`; its two-cell color-3
object is a distractor. Query 1 should return the smallest orange object's tight
cyan crop; the implementation computes that rather than relying on a fixed
position or memorized output shape.

**Remaining uncertainty.** The examples strongly support 4-connectivity and a
unique orange minimum. They do not independently establish behavior on ties or
inputs with no orange cells; those cases are outside the visible grammar, and
the implementation uses deterministic/empty fallbacks only to avoid crashing.
