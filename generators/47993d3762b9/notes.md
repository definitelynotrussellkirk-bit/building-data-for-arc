# Working notes: 47993d3762b9

The canonical generator and Racket authority remain unchanged: every nonzero
color's global bounding box contributes four corners. The retained canonical
distributed-extrema examples are essential; two observed endpoints are not an
adequate substitute for all cells of the color.

## Current parametric proposal

`workspace/parametric/` adds one episode-fixed `mode`: `all_corners` (exact
canonical program), `largest_bbox_frame`, or `smallest_bbox_frame`. The latter
two compute per-color global boxes and areas, select the extreme-area box, and
paint its perimeter in its original color. A's input-derived selected color and
bounds determine B's output color, location and geometry. This is contextual
selection followed by geometric completion, not iterative simulation.

The proposal deliberately excludes overlapping boxes and tied areas. It supports
2–6 demonstrations, normally three, and 1–4 independently counted novel queries.
The same seed yields identical inputs across modes; query inputs do not depend
on the demo count. The four query shapes are 9×11, 17×24, 24×26 and 30×30, in a
seeded order independent of settings and requested counts. This avoids assigning
one size permanently to the last turn while preserving one-query prefix identity.
Large cases contain four large clouds with foreground at all four canvas edges,
interior and edge distractors, and long output frames; they are not padded small
examples. Canonical production remains on its original 7–14 size controls.

Two constructive initial demonstrations combine distributed extrema, unequal
box areas, opposite pixel-count rankings, and changed selected colors. Their
dimension/count inequalities survive a joint color permutation and symmetry.
Later demos and queries vary density, texture and box geometry. Public projection
uses the shared visible-byte serializer and exposes exactly one query. It hides
settings, programs, answers, seeds, future inputs and total-query hints; the
existing consumer controls turn progression.

Focused tests live in `tests/test_parametric_47993d3762b9.py`. The reusable
`workspace/parametric/audit.py` retains executed labels and demonstration-only
finite-rival checks in `workspace/parametric/evidence/final-audit/`. Native inventory
is `workspace/parametric/evidence/manifest.json`; qualification and causal replay
are returned in the main task's checks directory. Tests and finite replay do not
prove universal identifiability, measured learning benefit, owner acceptance or
training admission. The next owner action is qualification and acceptance on the
exact integrated source after reviewing the parameter meaning and causal witness.
