# 2b7bcfbf942b — bounding-box checker completion

Version `3.0.0`; canonical rule hash `de72b7a33ad3`.

A zero-background grid contains one to three nonoverlapping, distinct-color,
4-connected objects.  Each object is a complete rectangular frame, a frame
with one open side, or a cross, and spans a bounding box of at least `3x3`.
The output replaces every object by its full bounding-box border and fills the
strict interior with a local same-color/zero checkerboard whose interior
upper-left cell is colored.

The default curriculum cycles `frame -> open -> cross`, so every three
consecutive sample indices contain a direct counterexample to the
canonical-demo shortcut “transform complete frames only.”  Canvas dimensions,
object count, positions, colors, bounding-box dimensions, orientation of open
sides, and horizontal/vertical layout vary independently subject to fit.
Canonical-size profiles are regularly revisited without restricting the full
advertised domains.

Exact axes:

- `grid_h`: `8..16`
- `grid_w`: `9..18`
- `n_objects`: `1..3`
- `object_style`: `frame|open|cross`

The generator declares executable canonical shortcuts, lesson competitors,
semantic witnesses, and `lesson_identifiable`.  The task-local probes are in
`workspace/reference_probe.py` and `workspace/lesson_probe.py`.
