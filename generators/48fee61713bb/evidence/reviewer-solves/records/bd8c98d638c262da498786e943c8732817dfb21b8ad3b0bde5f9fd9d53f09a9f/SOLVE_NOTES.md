# Solve work log

## Exposure declaration before solving

I had not opened task `48fee61713bb`'s generator, Racket rule, reference
solution, prior notes, audit records, or private labels. I had only read the
packet-wide instructions and the visible `solve-blind/challenge.json` created by
`solve_episode.py blind prepare`.

## Observations and hypothesis

Each 30x30 input contains hollow 3x3 colored tiles on a 7x7 lattice. A solid
edge of color 1 marks one side. The lattice always has a completely blank
middle gutter: column 3 when the marker is top/bottom, and row 3 when the marker
is left/right. Removing that gutter makes a 7x6 or 6x7 tile-level grid.

Comparing the three visible outputs to this gutter-removed grid showed that
nonzero tile colors retain their order but are compacted along each line:

- top marker: compact every row to the right;
- bottom marker: compact every row to the left;
- left marker: compact every column upward;
- right marker: compact every column downward.

For example, in the first training pair (top marker), a tile-level row
`..58.8` becomes `...588`; in the third pair (bottom marker), `8.8.5.` becomes
`885...`; and in the right-marker pair each column's colors fall to the bottom.
This accounts for every visible output cell without recoloring or sorting.

## Probe and implementation

I wrote a small visible-only Python probe that decoded each 3x3 tile into one
macro cell, printed the 7x7 macro inputs, removed the blank gutter, and compared
line-by-line compaction with the displayed training outputs. All three examples
matched the same directional rule.

`solution.py` therefore:

1. detects which outer edge is all 1s;
2. decodes the 7x7 lattice using the edge-dependent one-cell margin;
3. removes the known middle gutter;
4. stably compacts nonzero colors in the direction implied above.

The extraction scans each 3x3 block for its nonzero color rather than assuming a
particular colored pixel, and compaction preserves color order. I did not need a
failed program revision; the visible examples consistently supported this rule.

## Remaining uncertainty

The examples cover top, bottom, and right markers; the first query is the only
left-marker instance. Left/up is inferred as the rotational counterpart of the
right/down case and is also consistent with the top/right and bottom/left pair.
Private query labels were not consulted.
