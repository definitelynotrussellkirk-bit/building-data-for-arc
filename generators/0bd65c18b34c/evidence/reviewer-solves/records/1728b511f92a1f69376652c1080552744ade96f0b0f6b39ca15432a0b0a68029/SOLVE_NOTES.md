# Solve work log

During this solve DO NOT consult the Racket rule, generator implementation,
reference solutions, private query labels, or earlier solution explanations.
Use only challenge.json, your own Python, and the check command's feedback.

Record what you saw before this step, especially earlier Racket-rule exposure.
For each revision, summarize your hypothesis, probes/commands, observed results,
why you changed the program, alternatives, and remaining uncertainty. Describe
your reasoning in your own words; preserve failed ideas as well as successful ones.

## Revision 0 — hypothesis before implementation

Observed four disjoint 2×2 objects of color 2 in every training grid and fifteen
single cells of color 1. The output preserves the 2×2 objects and the count of
color-1 cells. A color-1 cell that shares either occupied row or occupied column
with a 2×2 object is translated along that row/column to the nearest empty cell
immediately outside the object. Unaligned color-1 cells remain fixed.

Probe: enumerated coordinates and input/output set differences from
`challenge.json`; every moved marker matched one such row/column alignment. I
will choose the closest candidate if a marker is aligned with more than one
object, while retaining the original marker when there is no candidate. The
visible-example regression test was written before the implementation.

## Revision 1 — failed nearest-alignment implementation

The first implementation moved every aligned marker, choosing the nearest block.
The regression failed consistently. Coordinate diffing isolated three classes of
false moves: `(18,16)`, `(20,1)`, `(20,4)` in training pair 0; `(26,27)` in pair
1; and `(29,18)` in pair 2. Each is aligned with a block but has at least eight
empty cells between the marker and the block. Every marker that actually moves
has at most seven empty intervening cells. Thus alignment is range-limited; the
root cause was omitting the visible examples' exact radius boundary.
