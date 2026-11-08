# Solve work log

## Exposure declaration before solving

I had not opened task `84def340ce03`'s generator, canonical rule, notes,
solutions, private labels, or audit records. I had only read the packet-level
instructions and the visible `solve-blind/challenge.json`.

## Revision 1 — nested rings from 2×2 tiles

The output side length is `input_height * input_width / 2`. Therefore the output
has one concentric ring for every 2×2 input tile: an even `h×w` grid has
`h*w/4` such tiles and the square has twice that many rows/columns.

I compared the 4×6 example's six ring-corner tuples with its six row-major 2×2
tiles. They match exactly. The first tile `[[6,5],[5,0]]` is the innermost ring
with top-left/top-right/bottom-left/bottom-right colors `6,5,5,0`; the final
tile `[[9,3],[6,0]]` is the outer ring. Each side of a `2m×2m` ring splits into
two runs of length `m`, so each source tile colors one corner-centered L-shaped
sector of the ring.

Implemented that direct construction. Remaining uncertainty before checking:
only whether the generator ever supplies odd dimensions; all visible examples
are even and the inferred 2×2 tiling requires even dimensions.
