# Solve work log

## Exposure declaration before solving

I had not opened task `997c17fd6870`'s generator, canonical rule, reference
solutions, private labels, audit records, or prior solution explanations. I used
only `solve-blind/challenge.json` and local Python reasoning.

## Revision 1 — reverse 2-column macro-cells

### Observation

All visible grids have even width. The colored pixels decompose naturally into
2×2 macro-cells aligned to even row/column boundaries. In the outputs, macro-cell
rows stay fixed while the occupied macro-cell columns reverse order. Crucially,
the pixels *inside* each 2×2 cell keep their orientation, so this is not an
ordinary pixelwise left-right reflection.

For example, in the 16×16 lesson the leading cell
`[[4,5],[5,4]]` moves from macro-column 0 to macro-column 7 without becoming
`[[5,4],[4,5]]`. In the 14×14 lesson with repeated `[[4,0],[6,6]]`
cells, macro-columns 2,3,4,5,6 become 4,3,2,1,0, respectively.

### Hypothesis

Partition every row into adjacent width-2 chunks, reverse the sequence of
chunks, and concatenate them. This translates every aligned 2×2 macro-cell to
its horizontal mirror slot while preserving its internal pattern. Rows do not
move.

### Alternatives rejected

- Pixelwise horizontal reflection: contradicted by preserved cell orientation.
- 180° rotation or anti-diagonal reflection: contradicted because row positions
  and the 2×2 interiors are unchanged.
- Reversing only nonzero objects: unnecessary and less general; reversing all
  macro-cells also handles empty slots exactly.

### Implementation

`solution.py` validates a rectangular even-width grid, slices each row into
2-column chunks, reverses those chunks, and flattens them. No task-private data
or fixed dimensions/colors are used.

### Remaining uncertainty

The visible examples strongly identify width-2 horizontal macro-cell reflection.
The hidden queries appear to use the same even-width aligned representation, but
query correctness remains intentionally unavailable during this solve.
