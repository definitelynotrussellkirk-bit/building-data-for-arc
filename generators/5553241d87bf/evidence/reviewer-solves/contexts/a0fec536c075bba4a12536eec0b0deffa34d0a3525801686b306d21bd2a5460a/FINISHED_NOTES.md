# Solve work log

I had no earlier exposure to this task's generator, Racket rule, private labels,
or prior solution explanations. I used only the visible challenge and local Python
probes over its training pairs.

## Revision 1

**Hypothesis.** Full-zero rows and columns divide the grid into equal rectangular
tiles. The modal nonzero color is the tile background. Exactly one tile contains
an intact colored motif; other affected tiles are marked by one or more internal
zero cells (holes). The output removes every internal zero by restoring the
background and copies the intact motif, at the same local coordinates, into the
motif tile and every tile that had a hole. Completely clean tiles remain plain.

**Probe.** I enumerated the separator spans and printed, for every training tile,
its internal-zero coordinates, non-background colored cells, and output
non-background cells. In example 0 every hole-bearing tile plus the motif tile is
stamped, while the single clean tile is not. Example 1 has the same behavior with
a different grid orientation and a multi-hole corruption pattern. Example 2 has
only two hole-bearing tiles among many clean tiles; exactly those two and the
motif tile are stamped. The motif's local geometry is preserved in all cases.

**Alternatives rejected.** Copying the motif to every tile fails on the clean
tiles. Row-wise or column-wise propagation does not explain the sparse placements
in example 2. Treating zeros as motif pixels would incorrectly preserve random
holes; the outputs instead replace them with the background.

**Implementation.** Infer all-zero separator rows/columns, contiguous tile spans,
and the modal nonzero background. Find the unique tile containing a nonzero
non-background color. Rebuild every tile as background, then overlay the motif on
the source tile and on each tile that contained an internal zero. Preserve the
separator lines.

**Remaining assumptions.** The visible task has one-cell zero separators, equal
tile sizes, one motif tile, a nonzero background, and zero as the corruption
marker. All visible examples satisfy these assumptions.
