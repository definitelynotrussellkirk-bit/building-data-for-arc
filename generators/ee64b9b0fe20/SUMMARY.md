# ee64b9b0fe20 — size-sort and bottom-pack objects

Version **3.1.0**, normalized canonical `RULE_HASH=e0863705f64c`.
Find the nonzero modal field. Extract monochromatic four-connected objects,
discard components whose bounding box spans the full canvas, sort by cell count,
and pack their bounding boxes left-to-right, bottom aligned. Preserve holes,
color and orientation. A shape touching an edge is not automatically a frame.

The generator supports 10..18 rows/columns in every difficulty band, 2..6
exactly placed objects with distinct sizes up to 12, optional frames, zero-valued
objects, repeated object colors and different-color contact. A shared canvas draw
puts 60% prior mass on 10x10 independently of the lesson phase. The generalized
branch can also draw 10x10; this is not an exact per-batch quota.

Every two consecutive default samples cover both frame states and refute four
executable rivals: bounding-box-area sorting, grouping disconnected objects by
color, fixed background 7, and incorrectly preserving an enclosing frame. The
area/grouping rivals fit only the three original demonstrations, not every
canonical variant; fixed-background-7 is the strongest declared shortcut that
fits all labeled canonical pairs. Explicit overrides opt out of the lesson
promise, never out of validity.

Real overrides: `grid_h`, `grid_w`, `shape_count`, `bg_color`, `frame`,
`palette_size`, `texture`. Palette size must not exceed shape count. Unsupported
or misspelled axes raise. `seed` and `sample_index` must be literal integers,
`sample_index` must be nonnegative, and difficulty must be one of `None`,
`easy`, `medium`, or `hard`.

Authoring probes and explicit regression commands are in `workspace/README.md`.
The separate `workspace/parametric/` prototype explores ascending versus
descending size order without changing canonical production or authority.
Approval remains a catalog/intake decision; this review does not set it.
