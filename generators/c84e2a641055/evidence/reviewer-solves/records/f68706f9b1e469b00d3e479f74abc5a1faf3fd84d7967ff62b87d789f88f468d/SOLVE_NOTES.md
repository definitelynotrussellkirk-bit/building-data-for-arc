# Visible-only solve notes

The four visible pairs preserve the grid dimensions, all colors, and every
relative coordinate inside the nonzero pattern. The only change is one shared
vertical translation: the lowest occupied input row becomes the final grid row.
The two multicolor examples are especially decisive because differently colored
cells retain their relative positions rather than falling independently.

The solution therefore collects all nonzero cells, computes
`shift = height - 1 - max_occupied_row`, and writes every cell at the same column
and `row + shift` in a fresh zero grid. An empty grid is copied unchanged.

This is a human-readable work log based only on the visible challenge prepared
for this episode. I had earlier exposure to the rule while reviewing the
assigned generator, so the episode is correctly declared exposed; I did not
consult the generator, Racket source, private labels, or reference solution
during this solve phase.
