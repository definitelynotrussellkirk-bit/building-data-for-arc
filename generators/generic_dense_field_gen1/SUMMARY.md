# generic_dense_field_gen1

gen1: LEARN A COLOR REMAP and apply it across a fully-colored grid.

Transform: every cell's color is mapped through a fixed bijection over the
palette (`recolor-map`), applied simultaneously to the whole grid. The input is
a 100%-filled grid of a few large contiguous color regions; the output is the
same grid with every color swapped per the learned map. The model must infer the
bijection from the demo pairs and apply it to the query.

Density concept: a DENSE (fully colored), LOW-component field — directly closes
the eval fill-density gap (eval ~73% filled vs the pool's old ~12%).

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
