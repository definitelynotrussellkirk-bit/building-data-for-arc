# 9bde2c3e0346

Two or three separated, single-color objects appear on a zero background. For
each four-connected object, the output is the one-cell-thick border of that
object's axis-aligned bounding box, rendered in the object's color on an
otherwise blank grid. Original interior pixels are erased; missing border pixels
are added.

The sampler is version `3.0.0` and exposes three exact controls: `grid_h` and
`grid_w` in `8..12`, and `n_objects` in `2..3`. Every ordinary generated input
contains both a missing border pixel and an original interior pixel, so a single
example distinguishes the selected rule from identity, solid-fill,
existing-border-only, and “add the frame but keep the interior” rivals. Canonical
8×8 and 9×9 two-color profiles are deliberately weighted in every difficulty
band while the full declared axis domain remains reachable.

Kind: `per_puzzle`. The selected canonical Racket rule is unchanged and pinned by
`RULE_HASH = "8f9e53b42241"`.
