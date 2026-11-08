# Blind solve work log

## Exposure declaration before solving

I had not opened task `cdb267535df8`'s generator, Racket rule, notes, prior
solutions, audit records, or private query labels. I used only
`solve-blind/challenge.json` and my own local analysis of its visible examples.

## Revision 1 — geodesic Voronoi fill

**Observation.** Gray (`5`) cells stay fixed and form walls. Every other
nonzero color acts as one or more seed points. Background cells are colored by
the nearest seed color when distance is measured by four-neighbor paths that
cannot cross gray cells. Multiple seed points of the same color form a
multi-source region. Cells exactly tied between different colors stay black
(`0`).

**Probe.** I implemented that rule in an independent scratch calculation and
compared it cell-for-cell against all three visible training outputs. It matched
every visible output cell (0 mismatches in each example). This also explains the
apparently irregular boundaries and the black tie lines.

**Implementation.** Run one breadth-first search per seed color over all
non-gray cells, then fill each original zero cell only when one color has a
strictly smaller distance than all others. Preserve gray walls and original
seeds.

**Alternatives rejected.** Ordinary Manhattan Voronoi distance fails where gray
walls force detours. Unrestricted flood fill cannot explain multiple colored
regions in one connected non-gray component. Treating every seed separately
would incorrectly create ties between two seeds of the same color.

**Remaining uncertainty.** None on the visible examples. The test outputs remain
masked, so the final claim is only that the inferred rule exactly reproduces
all visible pairs.
