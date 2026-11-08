# Solve work log

Earlier exposure: **yes**. I had inspected this task's generator and selected rule while repairing it before this required post-repair episode. During this solve episode I kept the generator, Racket source, canonical/reference files, private labels, and prior solution explanations closed; I used only the prepared visible examples and my own code.

## Revision 1 — smallest monochrome four-connected object

The first example contains four monochrome objects with 2, 3, 4, and 5 cells; the output is the exact two-cell object. In the other examples, a color can appear in more than one disconnected object, so total color frequency is not the criterion. Their outputs preserve holes/zeros inside the selected object's bounding box rather than filling the box.

Hypothesis: split nonzero cells into same-color, orthogonally connected components; choose the component with the fewest cells; crop and translate exactly that component to its bounding box. I used top-row/left-column ordering only as a deterministic tie fallback because the visible examples have a unique minimum. The code deliberately keeps diagonally touching same-color regions separate and edge-touching different colors separate.

Expected query behavior from the visible grids: query 0 selects the two vertical color-3 cells. Query 1 selects the five-cell lower color-4 component, not all color-4 cells and not the compact color-9 block. Remaining uncertainty is limited to an unseen equal-size tie, which the examples do not establish; the implementation uses reading order.
