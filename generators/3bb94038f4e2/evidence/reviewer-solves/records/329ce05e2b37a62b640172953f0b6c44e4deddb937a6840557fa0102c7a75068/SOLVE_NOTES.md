# Solve work log

## Exposure declaration

Before this solve I had not opened the task generator, its Racket rule, any
reference solution, private query labels, prior solution notes, or any generator
assigned for repair/audit. I used only the visible examples printed by
`python3 review.py blind prepare` and the public challenge files.

## Revision 1

Observed change locations were exactly the zero cells in horizontal `1,0,1`
triples. This also explains multiple simultaneous edits in rows such as
`1,0,1,0,1`: both original one-cell gaps are filled. Rows with wider gaps
(`1,0,0,1`) and adjacent pairs remain unchanged. Nonzero middle cells, such as
the color-2 separator in one training example, are not overwritten.

I considered two broader alternatives: connecting every pair of 1s on a row,
and filling only the unique three-marker row. The first is contradicted by the
unchanged wider-gap rows; the second is contradicted by the example where two
additional two-marker rows are also filled. The implementation therefore scans
the original grid once and writes color 1 only into zero cells whose immediate
left and right neighbors are both color 1. It deliberately does not iterate,
so a new fill cannot create longer propagation unsupported by the examples.

Remaining uncertainty: the visible examples do not show ragged rows, but ARC
grids are rectangular; the implementation still treats each row independently.
