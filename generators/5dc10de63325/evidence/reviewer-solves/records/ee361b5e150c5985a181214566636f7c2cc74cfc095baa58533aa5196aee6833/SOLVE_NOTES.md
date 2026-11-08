# Solve work log

## Exposure statement

Before this solve I had read only packet-level workflow documents and the visible
challenge printed by `review.py blind prepare`. I did not open this task's
generator, canonical rule, reference solution, private labels, notes, or audit
evidence.

## Revision 1 — diagnostic red state

Command:

```sh
python3 review.py blind check --intent diagnostic_probe --note \
  'Baseline harness probe: confirm the untouched solution template fails before implementing the count-based hypothesis.'
```

The untouched template raised `NotImplementedError`, giving 0/10 visible passes.
This was a harness/TDD probe rather than a proposed solution.

## Revision 2 — complete quartets encoded in a repeated tile

Visible observations:

- Every output is 5×5 and consists of the same 2×2 tile copied at offsets
  `(0,0)`, `(0,3)`, `(3,0)`, and `(3,3)`, with row 2 and column 2 left zero.
- The input geometry varies substantially while the output depends consistently
  on the number of azure (`8`) cells.
- Input counts 4, 6, and 7 produce one filled cell per tile; counts 8 and 10
  produce two; counts 13, 14, and 15 produce three; count 16 produces four.
  Equivalently, the number of filled tile cells is `floor(count(8) / 4)`, capped
  by the tile's four-cell capacity.
- Tile cells fill in reverse row-major order: bottom-right, bottom-left,
  top-right, top-left. Thus the four observed tile states are
  `[[0,0],[0,8]]`, `[[0,0],[8,8]]`, `[[0,8],[8,8]]`, and all eights.

I considered shape extraction and bounding-box compression, but examples with
scattered cells and solid bars share outputs solely by count bands, while equal
or nearby counts with unrelated geometry agree. The count law is therefore the
simplest hypothesis consistent with all ten visible examples.

For the queries, counts 19 and 5 imply four and one filled tile cells,
respectively. Remaining uncertainty: the visible data does not show counts below
4 or above 19, so capping at four is inferred from the fixed 2×2 tile capacity.
