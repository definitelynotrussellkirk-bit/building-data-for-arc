# Native source-order family

`row_major` is the selected canonical Racket program byte-for-byte.
`column_major` keeps frame recognition, exact size matching, nonzero-only copying,
source retention, and value-based one-use fixed, but orders loose source crops by
bounding-box column then row.

Every scene contains two equal-size frames and two unequal matching crops placed
so row-major and column-major source order disagree. The first frame assignment
updates the full-value `used` set; the second frame consumes that derived state.
`column_major_reuse.rkt` is the protected causal counterfactual that removes this
state update and consequently reuses the first column-major source.
