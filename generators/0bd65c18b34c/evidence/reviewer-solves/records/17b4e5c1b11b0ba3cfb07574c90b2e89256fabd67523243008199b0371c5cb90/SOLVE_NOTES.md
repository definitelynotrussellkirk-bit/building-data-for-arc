# Solve work log

Earlier exposure: I had not opened task `0bd65c18b34c`'s generator, reference
rule, private labels, prior solutions, notes, or audit records. I used only the
prepared `challenge.json` and local Python comparisons of its visible pairs.

## Revision 1 — nearest aligned block

**Observation.** Color 2 always forms separated 2×2 blocks. A color-1 singleton
changes only when it shares one of a block's two rows or one of its two columns.
Changed singletons move along that row or column until they occupy the cell
immediately beside the block. Unaligned singletons stay fixed. Where two blocks
share the same pair of rows, the examples send each singleton to the nearer
aligned block.

**Probe.** I enumerated all changed coordinates in the three visible training
pairs. Every removal/addition paired into the same row or column and terminated
one cell outside a color-2 block; unchanged color-1 cells had no such alignment.
I also wrote a small visible-pair regression harness and confirmed the untouched
solution template failed with `NotImplementedError` before implementing.

**Program.** Find 4-connected color-2 components, treat each component's bounding
box as a block, enumerate row/column-aligned destinations for every color-1 cell,
and choose the candidate with the smallest distance to a block edge. Apply moves
simultaneously so source order cannot affect the result.

**Remaining uncertainty.** The visible examples do not specify a tie between an
equally near horizontal and vertical candidate, nor collisions where two markers
would land on the same cell. The implementation uses stable lexicographic tie
breaking; the observed task distribution avoids both cases.

## Revision 2 — preserve the one-or-three satellite contract

**Failure evidence.** The first local visible-pair regression failed on exactly
two cells in training pair 0 and two in pair 2. It incorrectly moved `(8,1)`
toward the first block in pair 0 and `(10,23)` toward the first block in pair 2.
Both were aligned noise. This ruled out “move every aligned singleton.”

**Root-cause pattern.** Assigning each color-1 cell to its nearest aligned block
gives per-block candidate counts of `4,3,3,1` in pair 0, `1,1` in pair 1, and
`2,3,3,3` in pair 2. The outputs retain `3,3,3,1`, `1,1`, and `1,3,3,3`
respectively. Thus each block has one or three true satellites, while an extra
random singleton can accidentally occupy an aligned ray. In every ambiguous
visible case, the noise item is the farthest assigned candidate.

**Change.** First assign each singleton to its nearest aligned block. For each
block, move the nearest one candidate when fewer than three candidates are
present; otherwise move the nearest three. This is the smallest rule that fits
all three visible examples and preserves the observed one-or-three contract.
The held-out inputs have candidate counts `1,3,3,3` and `1,4,3,3`, so the rule
makes a concrete prediction rather than special-casing training coordinates.
