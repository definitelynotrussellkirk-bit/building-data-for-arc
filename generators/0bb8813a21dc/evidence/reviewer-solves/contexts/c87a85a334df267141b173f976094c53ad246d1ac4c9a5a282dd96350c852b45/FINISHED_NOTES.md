# Blind solve: 0bb8813a21dc

Only the public examples and query inputs displayed by `review.py blind prepare`
were consulted. No generator, rule, canonical labels, earlier explanations,
task notes, or audit evidence has been opened, including the repair target.

## Visible observations

The three training pairs have shapes 4x7 -> 4x7, 4x6 -> 4x6, and
4x7 -> 4x7. The zero mask and all row lengths stay fixed. Each nonempty
output row has a single nonzero color, equal to the leftmost nonzero input
in that row. Entirely empty rows remain empty.

## Hypothesis and discriminating probes

Recolor every nonzero cell in a row using its first nonzero color.
The majority-color alternative is contradicted by training example 0 row 1:
6 occurs once, 4 occurs twice, but the output uses 6. Training example 2
row 3 similarly chooses 3 over the repeated 6. The rightmost-color alternative
is contradicted by those same rows. A whole-grid shared color is ruled out
by outputs containing differently colored rows.

The implementation handles leading zeros, interior gaps, nonuniform rows,
and empty rows without assuming an input width or height. The two query
inputs are 5x6 and 4x7; their outputs and output dimensions are unknown.

## Revision 1

Implemented the row-local leftmost-nonzero hypothesis directly. This is a
genuine first solve attempt; no deliberately incorrect version was created.
The official checker will assess visible examples and execution only.
Masked-query correctness is reserved for independent maintainer scoring.
