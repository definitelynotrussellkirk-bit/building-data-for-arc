# Blind solve work log — 019445e9b5a1

## Exposure and inputs

I read the packet routing instructions, ordered duties, and the visible grids
printed by `python3 review.py blind prepare`. I have not opened any generator,
rule, task notes, reference solution, audit, or hidden query label. The three
visible examples have shapes 4×8 to 4×8, 6×9 to 6×9, and 7×7 to 7×7.
The two query inputs are 4×8 and 5×10; their output shapes are unknown.

## Revision 1 — left-border row recoloring

Hypothesis: when the first cell of a row is nonzero, recolor every nonzero cell
in that row with the first cell's color. Preserve zero cells. Rows beginning
with zero are unchanged.

Evidence: example 0 row 2 has a 9 at column 0 and a 2 at column 6; the latter
becomes 9. Example 1 row 4 changes 3 to 5, even though neither color is repeated.
Example 2 row 0 changes 3 to 5 while row 3 (beginning with zero) retains both
8 and 9. The last observation rules out recoloring every row by its leftmost
nonzero color. Example 1's last row provides another counterexample to that rival.
The empty cells are preserved throughout, ruling out filling horizontal gaps.

I considered choosing the most frequent nonzero color per row, but a singleton
left-border anchor already directs recoloring in examples 0 and 1. This supports
the positional interpretation. No failed executable solution has been submitted;
the alternatives above were hypotheses checked directly against visible pairs.

Implementation uses a fresh nested list so the input is not mutated. Verification:
`python3 review.py blind check --intent solve --note 'Left-border nonzero anchor recolors nonzero cells in its row; rows with a zero first cell and all zero positions are preserved.'`
The checker supplies only visible-pair and execution feedback. Query correctness
will remain unknown until independent maintainer scoring.
