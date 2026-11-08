# Local 3x3 window corner union

Task `a06827026857`; sampler version `3.0.0`; unchanged Racket rule hash `4f871ddb0a9d`.

Start with a blank output. For every solid monochrome nonzero 3x3 window in the
original input, paint that window's four corners in its own color. Union all
such corners; discard all unmatched foreground.

The sampler alternates canonical-scale separated squares with mixed examples
that contain repeated colors, an orthogonal corner appendage, and an overlapping
3x4, 4x3 or 4x4 block. Default mixed base counts vary by difficulty. Exact controls
are `grid_h`, `grid_w`, `square_count`, and `case`; invalid or incompatible tuples
raise rather than returning a partial construction. See `notes.md` for limits.
