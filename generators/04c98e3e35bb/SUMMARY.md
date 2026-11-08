# 04c98e3e35bb

Kind: `per_puzzle`. Selected generator version: **3.2.0**.
Canonical Racket rule pin: **`264a1a87abe5`**.

## Rule and input domain

Background is the fixed color **0**, even when another color is more frequent.
Objects are **same-color, four-connected components**. Recolor every cell of a
component to **2** if any component cell touches a grid edge; otherwise recolor
it to **8**. Background cells stay 0. Different-color orthogonal contacts and
same-color diagonal contacts do not merge components. Input colors **1..9**,
including 2 and 8, are legal.

Production inputs have dimensions 6..25, background present, and at least one
border component and one strictly interior component. Generated inputs have
one to four components of each class. Validation accepts larger component
counts within the same grid domain, including all four canonical inputs.

## Generation API

`generate(seed, sample_index, *, difficulty=None, **overrides)` is deterministic.
Difficulty is `easy`, `medium`, `hard`, or `None`. Explicit integer controls
reject booleans, floats, and strings; unknown axes fail visibly. `None` values
mean no override.

| Control | Contract |
|---|---|
| `grid_h`, `grid_w` | Exact dimensions, each 6..25, in every difficulty band |
| `n_border_objs`, `n_interior_objs` | Exact observed same-color four-component counts, each 1..4 |
| `obj_color` | Exact color 1..9 of the first occupied cell in row-major order |
| `mixed_colors` | Boolean or integer 0/1; false gives one foreground color, true gives at least two |
| `texture` | `mixed`, `rect`, `L`, `T`, `plus`, `blob`, `line`, or `single`; `obj_shape` is a checked compatibility alias |
| `obj_size_min`, `obj_size_max` | Random construction scales, respectively 1..5 and 2..6; minimum must not exceed maximum |

Size controls are not exact cell counts or bounding-box bounds. T has an
intrinsic minimum scale of 3; L, line, and plus have a minimum of 2. Mixed texture
includes singletons; explicit singleton/size combinations are refused. Explicit
shapes are never silently shrunk. Bounded packing either realizes all requested
counts or raises an incompatibility naming relevant axes.

## Default curriculum and limits

The 16-index semantic schedule uses **75% contact motifs and 25% free layouts**.
Contact profiles cover 6×6, 7×7, 8×8, and 7×9 in every difficulty band. They use
border/interior L components, a different-color bridge, interior colors 2 and 8,
and an isolated same-symbol border domino or singleton. A conditional one-cell
border extension makes the main border component win a largest-component,
row-major-tie selection; otherwise the L components remain congruent. These
distinguish nine declared rivals, including independently authored
`degree_two_loop` and `largest_component` heuristics. `EXAMPLES_NEEDED` is 3;
lesson checks use actual demonstration labels and do not inspect masked query
labels.

Any nonempty effective override selects free packing and loses the default
lesson guarantee. Free layouts broaden shapes, positions, palettes, and aspect
ratios. The default distribution still favors its repeated motif and mandatory
interior 2/8 witnesses. Finite rival checks do not prove unique identification
among all programs. The v3.2.0 battery passed all 12 stages and portable tests
passed 113/113. The 300-lesson census and 48-window fixed-seed schedule had zero
ambiguity, warnings or errors against nine rivals in production and every
tested rotation. Approval remains derived by the catalog from current source
and retained evidence.

Owner acceptance: current repaired source is retained with reviewer-reported checks; audit-only findings remain source-bound with their target generators. No model trajectory is training-admitted.
