# Solve work log

## Exposure record

Before this solve episode I had reviewed the generator family, so earlier rule
exposure is **yes**.  After `solve prepare` I consulted only the visible
`challenge.json`/README and this solve directory; I did not reopen the
generator, Racket source, reference solutions, private labels, or earlier solve
notes.

## Visible-example inference

All three examples contain two nonzero colors.  One color is a singleton marker
and the other forms a larger support object plus harmless disconnected noise.
The marker has exactly one cardinal background neighbour:

- example 0: opening right; a new marker appears left of the support;
- example 1: opening left; four markers appear to the right boundary;
- example 2: opening up; one marker appears below the support.

This supports one direction-independent rule: take the ray opposite the unique
open side, preserve its nonzero support cells, and recolor all background cells
on that ray through the boundary with the marker color.  It also rejects a
palette-to-direction lookup because the three examples use different marker and
support colors while the geometry alone determines direction.

## Implementation

`solution.py` finds the unique singleton nonzero color, verifies that its marker
has exactly one open cardinal side, reverses that direction, and changes only
zero cells along the resulting ray.  It validates empty/nonrectangular or
ambiguous inputs rather than silently selecting a candidate.

Expected visible-query effects before checking:

- query 0: marker 5 at `(8,16)`, opening right, so fill row 8 columns `0..12`;
- query 1: marker 7 at `(9,2)`, opening down, so fill column 2 rows `0..6`.

No alternate implementation revision was needed before the first check; the
three visible examples jointly determine the direction and extent.
