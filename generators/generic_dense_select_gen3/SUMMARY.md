# generic_dense_select_gen3

gen3: KEEP ONLY THE ODD-ONE-OUT shape, erase the repeated ones.

Transform: the field holds several identical copies of one base shape (varied
colors) plus exactly one object of a DIFFERENT shape. `pick-unique` with
`same-shape?` returns that lone object — the one whose shape-equivalence class
is a singleton — and we erase every other object, leaving only the odd one.

Selection concept: keep the unique object that differs from all the rest.

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
