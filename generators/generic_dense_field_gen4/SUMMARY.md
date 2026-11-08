# generic_dense_field_gen4

gen4: DENSE DOWNSCALE — collapse a zoomed-in, fully-colored field.

Transform: the input is a 100%-filled grid built of uniform K x K blocks (a
small dense partition upscaled by K); the rule downscales by K, recovering the
small grid. Program: `(downscale g K)` (no fn -> takes each block's top-left
cell, which is the block color since blocks are uniform -> byte-exact parity).

Why this gen (vs resize/gen2's downscale): resize/gen2 fills its small grid only
~60% (40% background), so its INPUT is sparse. This one's input is FULLY filled
by a few large regions, so it closes BOTH gaps at once -- fill DENSITY (eval ~73%
vs pool's old ~12%) AND the size-SHRINK gap (output smaller than input, ~0 in the
pool) -- while keeping a LOW component count (eval-like, not pixel noise). The
hard tier reaches the large-grid tail (input up to ~27 wide, fully colored).

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
