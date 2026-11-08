# generic_jigsaw_pack_gen1

gen1: reverse-built jigsaw scenes.

Scene: a random connected blob is partitioned into 3-6 connected pieces
by multi-source BFS growth; the blob (one color) sits on one side of the
grid, the pieces (distinct colors, occasionally two-toned) scatter on
the other side (different background). Transform: solve the exact tiling
and output the blob bbox padded by 1 with the pieces docked in place.
Scenes resample until the solver reproduces the intended tiling.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
