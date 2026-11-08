# Solve work log

Earlier exposure: none. I did not inspect any generator, rule, private labels,
reference solution, prior solve notes, or audit evidence before this solve.

## Hypothesis

All visible examples preserve the input and add a copy of every nonzero cell at
its transposed coordinate `(column, row)`, i.e. reflection across the main
diagonal. Examples include `(2,6)->(6,2)`, `(4,1)->(1,4)`, and
`(1,5)->(5,1)`, always preserving the source color.

## Probes and implementation

I first wrote a local test using two differently colored cells at mutually
transposed coordinates. That fixture was invalid for the inferred union rule:
it introduced a collision absent from every visible example. The resulting
assertion failure showed that the test expected replacement while the examples
only support addition. I discarded that fixture, restored the stub, and reran a
clean red test with one off-diagonal cell; it failed with the expected
`NotImplementedError`.

The implementation copies the grid, then fills each blank transposed coordinate
with the source color. Original cells take precedence if a conflicting nonzero
mirror ever occurs. No visible example contains such a conflict, so collision
behavior remains explicit uncertainty rather than an inferred requirement.

## Alternatives considered

A 180-degree reflection and corner completion do not explain train example 1,
while main-diagonal reflection explains every added cell in all three examples
without extra changes.
