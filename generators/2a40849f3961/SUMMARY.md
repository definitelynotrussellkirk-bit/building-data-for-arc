# 2a40849f3961 — ordered shortest paths through a maze

A zero-background grid contains gray (`5`) wall barriers and exactly one checkpoint of each color `1`, `2`, `3`, and `4`. For each consecutive pair `1→2`, `2→3`, and `3→4`, find a shortest 4-neighbor path through every non-wall cell. Breadth-first ties follow the selected authority's neighbor order: up, down, left, right. Recolor only zero-valued interior cells on the selected routes cyan (`8`); checkpoints and walls stay unchanged. An unreachable leg contributes no cells.

Version `3.0.0` replaces the former wall-filled, one-row corridor with a source-shaped mixture of irregular open mazes and explicit equal-shortest-path witnesses. Generated grids are 11–13 rows by 12–14 columns, use 3–8 separate wall components, and retain a long barrier at canonical scale. The production schedule alternates `canonical_maze` and `tie_break`; with three demonstrations and one query, every cyclic query rotation leaves at least one tie-break witness among the demonstrations.

The strongest retained canonical-fitting shortcut is identical BFS except for right-before-left priority (`up, down, right, left`). It fits every labeled canonical pair but disagrees on the generated `tie_break` profile. Exact axes are limited to `grid_h`, `grid_w`, and `scene_pattern`, all recoverable from pixels. The canonical Racket rule hash is pinned as `cd7f3a44d341`; its executable semantics are unchanged, while the selected source text was synchronized to the canonical authority.

Approval remains catalog-derived from current source and retained evidence; this summary is not an approval record.
