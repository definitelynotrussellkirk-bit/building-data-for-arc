# Native parametric family: `5c126cb64bf7`

`pattern_scope=whole` is the exact selected canonical program: crop and
binarize each complete 5-column panel, compare the three patterns under the four
rotations, and emit the 3×3 relation matrix. `pattern_scope=largest_component`
first extracts each panel's unique largest four-connected component, then uses
those normalized input-dependent intermediates for the same rotational relation
matrix.

Inputs are identical across settings for a fixed seed and request. The adapter
supports 2–6 demonstrations and 1–4 queries independently. Its two-demo prefix
contains (1) an all-equivalent case and (2) a chiral-core witness where the
whole-pattern, largest-component, reflection-permitting, and cell-count rules all
produce different matrices. The final fixed query is a boundary-spanning 30×17
case with 27 foreground cells. The bounded audit checks prefix stability,
matched inputs, seven named rivals, actual setting disagreement, and the
wrong-intermediate counterfactual. Native authoring preflight independently
executes every label through protected Racket.
