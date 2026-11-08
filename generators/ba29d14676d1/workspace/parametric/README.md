# Densest-tile reflection family

`tile_scope=all_tiles` returns the exact canonical Racket program and mirrors
all lattice tiles. `tile_scope=densest_only` first counts nonzero cells in each
tile, selects the unique densest tile, and mirrors only that tile. Inputs are
matched across settings. The sampler supports 2–6 demonstrations, four distinct
queries, multi-tile 29×29 stress, and a lawful exact 30×30 single-tile execution
stress (the latter is intentionally setting-degenerate because 30+1 is prime).

The causal witness replaces the densest intermediate with the sparsest tile and
requires a different protected-Racket output.
