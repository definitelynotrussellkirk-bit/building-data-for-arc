# generic_dense_field_gen2

gen2: MIRROR a fully-colored grid left<->right.

Transform: `(flip-lr g)` — reflect the dense field horizontally. The input is a
100%-filled grid of a few large contiguous color regions; the output is its
mirror. Teaches a geometric transform on a DENSE field (models routinely fail
geometry once the grid is fully colored rather than sparse).

Density concept: same high-fill / low-component envelope as gen1.

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
