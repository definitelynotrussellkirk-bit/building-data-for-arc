# Solve work log

## Exposure declaration before solving

I had not opened task `52ac31926856`'s generator, Racket rule, solutions, private
labels, notes, or audit records. Before the assignment draw I did accidentally
open an unrelated task's `NEXT_REVIEW.md` (`2c6496d261a6`) while surveying the
packet; it did not identify or describe this blind task.

## Revision 1 — intact aligned basin, otherwise bottom edge

Visible examples contain one color-1 marker above color-2 U-like structures.
The marker disappears. A solid U whose two walls bracket the marker column is
filled with color 1. Broken floors are skipped: training example 1 skips the
upper broken U and fills the lower intact U. In training example 2 both aligned
U shapes have a one-cell floor leak, so color 1 reaches and fills the bottom
edge.

I encoded this geometrically rather than by memorizing dimensions: enumerate
pairs of vertical color-2 walls bracketing the marker, require a fully joined
color-2 floor and an empty interior, then fill the first intact basin encountered
from top to bottom. If none exists, fill empty cells on the last row. A local
replay against all three visible training pairs passed before invoking the
packet checker.

Remaining uncertainty: unseen inputs might contain asymmetric wall heights,
obstacles on the bottom edge, or multiple simultaneously intact aligned basins.
The implementation preserves color-2 bottom obstacles and chooses the first
intact basin, matching the physical falling-liquid interpretation.
