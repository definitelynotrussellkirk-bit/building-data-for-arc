# Parametric family: `e5ead55c33e7`

The episode-fixed `packing_order` parameter exposes the sequential dependency in
the source rule:

- `front_first` — exact canonical rule: clear all movable objects, sort the
  rightmost object first, then slide and commit each object against the wall or
  the occupancy produced by earlier objects.
- `rear_first` — use the same clear/slide/commit process but sort the leftmost
  object first.

Every generated scene contains at least one row-overlapping collision chain, so
the first object's landed cells form an input-dependent intermediate consumed by
the next object's blocking test. Colors, shapes, horizontal order, band count and
canvas size vary; inputs are identical across settings. Two demonstrations are
sufficient, four queries are always retained, and the last query is a dense
three-band 30×30 stress case. Protected qualification replays all claim labels in
Racket.
