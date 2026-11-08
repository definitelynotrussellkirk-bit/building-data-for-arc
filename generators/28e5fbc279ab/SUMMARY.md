# 28e5fbc279ab

Select the unique largest 4-connected color-3 motif, normalize it at its
bounding-box origin, and copy it at every distinct-color singleton marker in
that marker's color. Preserve the complete input, including marker anchors,
empty motif corners, and any smaller green distractor.

Version 2.1.1 keeps the version-2 packing and exact override contract, and adds a
three-example lesson witness for the authority's largest-green-object selector.
The `free_shape` profile contains one disconnected green singleton whenever the
requested geometry has room. Its full lesson envelope is reserved at every
placement, so the real stamps and conservative union-of-green footprints both
fit and remain disjoint. Geometrically saturated explicit override tuples remain
lawful zero-distractor cases rather than silently changing an override.

Kind: `per_puzzle`. Rule pin: `20f1992162e5`; the canonical Racket authority is
unchanged. Effective axes remain `grid_h`, `grid_w`, `n_markers`, `motif_size`,
and `anchor_kind`. See `notes.md`, `workspace/README.md`, and task-local tests.

Approval is derived by the catalog and requires maintainer replay. Local checks
do not admit the generator for training.
