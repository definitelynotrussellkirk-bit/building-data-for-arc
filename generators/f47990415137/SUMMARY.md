# f47990415137 — bbox aspect, not color identity

Version 3.0.0. Recolor each monochrome 4-connected object by its bounding-box
aspect: tall → 2, wide → 3, square → 4; paint only original object cells.
The canonical Racket authority is unchanged and pinned by `RULE_HASH=5cf35af61edf`.

Generate 3–6 separated connected objects on 8–20-cell canvases. Defaults include
all three aspect classes, repeated input colors across different aspects, and
an irregular square-bbox object. The four exact controls are `grid_h`, `grid_w`,
`n_blobs`, and `n_distinct_colors`; each is recoverable from returned pixels.

Tests live in `tests/`; independent authoring probes live in `workspace/`.
See `notes.md` for migration and distribution limits. A passing review does not
change training approval; that remains a separate catalog/maintainer decision.
