# Solve work log

I began this solve with no exposure to task `3799ce10ce15`'s generator, Racket
rule, reference solution, private query labels, notes, or audit evidence. I used
only the visible examples printed by `python3 review.py blind prepare` and the
public challenge file.

## Revision 1 — framed-panel membership table

**Hypothesis.** The isolated colored cells above the panels form an ordered
legend. Every 9-bordered rectangle is one row of the output, in reading order.
For each legend color, the output repeats that color when it occurs anywhere in
the panel interior and writes 0 otherwise.

**Evidence from the visible examples.** In training example 0 the legend is
`[2, 7, 5]`: the first panel contains only 2, the second contains 7 and 5, and
the third contains all three, exactly matching the three output rows. Training
examples 1 and 2 independently match the same presence-table rule despite
different legend lengths, panel dimensions, and arrangements.

**Implementation.** Find each 4-connected component of border color 9, retain
components that are exact rectangular borders, sort them by top-left position,
read unique legend colors before the first frame, and emit the per-panel
presence table. A fallback reads non-frame colored cells if a future layout has
no legend row strictly above the frames.

**Alternatives rejected.** Color counts and exact positions inside a panel do
not affect the visible outputs: colors appear multiple times but are represented
once, and panels with different internal geometry yield the same membership
encoding. The remaining uncertainty is limited to unshown layouts where frames
touch or the legend is not outside/above them.
