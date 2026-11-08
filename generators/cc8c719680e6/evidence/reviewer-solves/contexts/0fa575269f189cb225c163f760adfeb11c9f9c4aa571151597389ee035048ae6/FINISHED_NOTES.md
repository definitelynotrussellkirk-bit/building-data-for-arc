# Solve work log

I had no earlier exposure to task `cc8c719680e6`, its generator, reference rule,
private labels, or prior solution explanations before this solve.

## Revision 1 — bounding-rectangle perimeters

Hypothesis: treat each nonzero 4-connected component independently. Replace all
of its cells by the perimeter of the component's axis-aligned bounding box,
keeping its color and leaving the rest of the grid unchanged.

Evidence from the visible examples:

- The color-3 object in train 0 has a 3×3 bounding box and becomes its eight-cell
  perimeter.
- The 2×3 and 3×2 boxes become completely filled because every cell is on their
  perimeter.
- Train 3 separates the two color-4 components despite their shared color. The
  lower 3×3 component loses its center cell while missing border cells are added,
  which rules out a fill-only interpretation and supports component-wise
  perimeter replacement.
- Four-connectivity is sufficient for every displayed object; no diagonal-only
  grouping is needed.

Probe: `/tmp/test_blind_visible.py` imports `solution.py` and compares `solve`
against all four visible training outputs. The initial template failed with
`NotImplementedError`, as expected. After implementing the component traversal
and perimeter rewrite, rerun this probe and the packet's visible-only checker.

Remaining uncertainty: the examples do not specify how overlapping bounding-box
perimeters of distinct objects should be resolved. No visible example or query
contains such an overlap, so the implementation preserves unrelated cells and
uses the natural component processing order if borders would collide.
