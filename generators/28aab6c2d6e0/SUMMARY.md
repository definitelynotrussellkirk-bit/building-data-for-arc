# 28aab6c2d6e0 — fill each object's bounding box

On a zero background, find every nonzero 4-connected monochrome component independently and
paint its complete tight bounding rectangle with that component's color on a fresh zero
canvas. Disconnected components of the same color remain separate objects; they do not share
a global color-level rectangle.

Generator version `3.0.0` produces canonical-scale 7–8 by 7–9 grids with exactly 2–4
pairwise-separated irregular components and exactly two nonzero colors. Every component
expands under the rule, every scene contains a non-L component, and every three-example
lesson contains a disconnected repeated-color counterexample to the tempting “one bbox per
color” shortcut. Exact observable controls are `grid_h`, `grid_w`, and `n_objects`.

Canonical Racket rule hash `c86a6d30fc9f` is unchanged. The selected repaired generator
SHA-256 is `ea24b149fc1cbf74819a3861454acad5ef8149170fef792bf69db03f0e546a2c`.
The final battery is 12/12 green, task-local tests are 11/11, and the retained 100-lessons-per-
band probe reports no surviving declared rival window. Approval remains derived by the
catalog; this summary is not an approval record.
