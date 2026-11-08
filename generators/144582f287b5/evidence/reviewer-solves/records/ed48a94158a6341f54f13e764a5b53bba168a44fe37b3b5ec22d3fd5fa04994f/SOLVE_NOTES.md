# Solve work log

This is a human-readable work log, not a token-level model trace. Before this
visible-only phase I had already inspected the assigned generator and canonical
rule while repairing it, so the final declaration must say earlier exposure
`yes`. During this phase I did not reopen the generator, Racket source,
reference solutions, private query labels, or earlier solution explanations.

## Revision 1 — fixed-offset source block

The three visible examples preserve the input shape, clear every output cell,
and copy four values to the four corners in row-major order. The copied values
are always the fixed cells `(1,1)`, `(1,2)`, `(2,1)`, `(2,2)` using zero-based
coordinates:

- example 0 copies `[[7,3],[8,1]]` to corners `7,3,8,1`;
- example 1 ignores the four input-corner decoys and copies
  `[[1,3],[4,7]]`;
- example 2 ignores the 9-valued halo and copies `[[1,2],[7,8]]`, showing that
  the source is not the geometric center on larger grids.

I implemented that exact shape-preserving scatter. The main alternative was
“take the geometric-center 2×2,” but visible example 2 directly refutes it:
its geometric center is not `[[1,2],[7,8]]`. Another alternative was “use the
first four nonzero values,” refuted by the decoys in examples 1 and 2.

Expected masked-query corner values from the visible inputs are `[1,4,8,2]`
for the 7×5 query and `[3,4,9,1]` for the 4×4 query. The check command is used
only for visible-example execution feedback; masked answers remain withheld.
