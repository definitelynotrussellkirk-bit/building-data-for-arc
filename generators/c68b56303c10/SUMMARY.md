# BBox overlap — c68b56303c10

On background 0, find the bounding boxes of all color-2 and all color-3 cells.
Return a solid color-8 rectangle with exactly their intersection's height and
width. The canonical Racket authority is unchanged (`42cdb52c8cce`).

Version 3.0.0 constructs sparse colored boxes around a chosen overlap. Exact
controls are height 7..18, width 8..22, and 2..8 points per input color in every
difficulty band. Canonical-scale canvases and output sizes remain weighted in
all bands. Three-demo lessons use a period-2 mix of broad geometry and repeated
counterexamples to four canonical-fitting shortcuts and five other rivals.

See `notes.md` for validator scope and finite-evidence limitations, `tests/` for
portable regressions, and `workspace/probe_distribution.py` for reproducible
source-bound distribution measurements. Passing checks do not admit model
trajectories to training.
