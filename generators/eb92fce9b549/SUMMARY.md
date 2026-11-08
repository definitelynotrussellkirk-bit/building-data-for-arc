# eb92fce9b549

Version `3.0.0`. A square zero-background grid contains 2–4 disconnected objects in one foreground color. The unchanged canonical authority ranks the objects by descending bounding-box area and repaints them 2, 3, 4, … on a blank grid.

The generator has two lawful layout families:

- `rings`: nested rectangular perimeters separated by a blank moat, preserving the canonical visual family;
- `scattered`: a constructive witness in which a sparse 3×3-bbox object has five cells and outranks a dense 2×3 object with six cells, refuting occupied-cell-count ranking.

Exact axes are `grid_size` (7–24), `n_objects` (2–4), `layout` (`rings|scattered`), and `foreground_color` (1–9). Defaults use canonical side lengths 7, 9, 11, 13, and 15. Every default three-example window contains a declared bbox-vs-cell-count witness.

Canonical rule hash: `45c25a11961c`. Approval remains catalog-derived; this review does not change it.
