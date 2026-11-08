# f2dbde875127 — keyed rotation and recentering

Version: `3.3.0`. Final generator SHA256:
`b3adc8e5389ad39d70f4b5dd9828f3352f9de1195c9d67f29139c7d5c3e10b92`.
Canonical Racket authority: unchanged (`f0178b249d84`).

A zero-background grid contains 1–3 separated blue rectangular frames. Each
frame contains one connected single-color object and has one key (2/3/4/5)
immediately above it. The unchanged authority rotates the object's cropped
bounding box by `(key-2)*90°` clockwise, clears the old interior, and centers the
rotated box with floor offsets. The frame and key remain unchanged. Square and
non-square interiors are both valid.

Ordinary draws use objects with four distinct normalized orientations and place
every object away from its eventual centered target. Thus the rotation/recenter
operation is visible for every key, including the zero-turn key 2. Semantic
validity is intentionally broader: canonical symmetric or already-centered
inputs remain accepted.

The episode contract now requests four visible examples. The first spatial frame
uses a deterministic per-seed/sample key schedule, so every four consecutive
samples expose keys 2, 3, 4, and 5. This addresses the reproduced lesson-level
failure where a query key was absent from all demonstrations. It is a finite
teaching contract under the declared independent-key rival family, not a proof
of general learnability.

All task-local free RNG streams are salted by difficulty. This prevents exact
same-seed/sample replay across easy, medium, and hard when their canvas support
overlaps. The final input-only probe measured 768/768 unique primary grids over
256 seeds × 3 bands, zero cross-band duplicate seeds, zero initially centered
objects, and 768/768 passing four-sample key windows.

Geometry is packed constructively; requested frame count is never silently
reduced. Exact override observations are canvas dimensions, frame count, maximum
interior height/width, and first spatial frame's key. Explicit interior/key pins
apply to every frame. One third of unpinned draws retain canonical-scale support;
the remaining draws preserve broader band-dependent geometry.

See `workspace/README.md`, the task-local tests, and the return packet's
`REVIEW.md` and `DECISIONS.md`. Passing review evidence does not grant training
admission; independent maintainer replay remains required.
