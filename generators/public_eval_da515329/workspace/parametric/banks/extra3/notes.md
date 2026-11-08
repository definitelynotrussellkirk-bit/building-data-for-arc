# public_eval_da515329 authoring notes

## Canonical rule

The input is a black canvas containing four equal, one-cell-wide arms around a
blank center.  Continue all four arms as one rotationally coupled clockwise
spiral.  At each step the upper arm prefers right, then straight, then left;
a candidate is legal only when its eight-neighborhood touches no earlier spiral
cell except the preceding two cells on that arm.  Rotate every accepted step by
90°, 180°, and 270° for the other arms, continue on the unbounded lattice, and
clip to the finite canvas.

`reference.rkt` is a general implementation and is byte-identical to
`workspace/parametric/canonical.rkt`.  It reproduces every supplied train and
gold-labelled test pair.

## Episode-fixed extension

`finish_rule=highlight_longest` first completes the clipped spiral, then groups
its line cells into four-connected components and recolors the unique largest
completed component with color 2.  The raw four arms are equal, so the selector
is defined only after completion and clipping.  The retained counterfactual
instead highlights the shortest completed component.

The sampler supports 2–6 demonstrations and 1–4 queries, keeps inputs matched
between settings, retains four private novel queries, privately permutes the
complete bank before taking a prefix, and contains a substantive 30×30 case.

## Evidence boundary

The task-local audit executes finite named rivals, protected-Racket labels,
private-field mutation checks, single-query public projections, and a source-
bound wrong-intermediate witness.  It is bounded reviewer evidence only: owner
registration, native qualification, acceptance, and any training admission are
separate and remain pending.
