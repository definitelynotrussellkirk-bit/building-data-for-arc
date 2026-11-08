# 6387de413b52 color-to-axis role family

`row_source=color2` preserves the exact canonical program: union the row ranges
of color-2 object bounding boxes, union the column ranges of color-3 object
bounding boxes, then paint their Cartesian product cyan (8). The proposed
`row_source=color3` setting swaps those two color roles while keeping the same
bbox extraction and cross-product operation.

Both settings receive identical deterministic inputs. The first two
illustrations contain multiple disconnected, nonrectangular blobs with separated
bbox bands, so occupied-cell, first-blob, global-bbox, same-color-for-both-axes,
and union-not-cross shortcuts are visible. The four-query bank is shuffled
before prefix slicing and includes a dense 30×30 scene with four components of
each role spread across all quadrants.

The input-dependent intermediate is the active row set and active column set;
the painter consumes those sets directly. Substituting the opposite color-role
intermediate changes the protected-Racket output. The adapter supports 2–6
demonstrations and 1–4 queries.
