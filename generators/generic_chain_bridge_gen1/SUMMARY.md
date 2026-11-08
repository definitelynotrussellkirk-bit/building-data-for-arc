# generic_chain_bridge_gen1

gen1: box lattices wired by a sequence strip.

Scene: a sparse lattice of framed boxes (one frame color; size 3 = single
core, 4 = 2x2 core, 5 = single core inside a frame-colored interior),
core colors mostly distinct with occasional duplicates; a strip of
isolated cells spells a non-revisiting WALK over the boxes. Transform:
bridge each consecutive pair through the clear gap along the earlier
box's core band, painted in the earlier entry's color. Scenes resample
until the rule's first-fit backtracker reproduces the intended walk.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
