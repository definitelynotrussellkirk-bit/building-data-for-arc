# Parametric row-policy family

This native two-setting family preserves the selected canonical program exactly
at `row_policy=all`.  Both settings first compute the aligned separated-panel
NOR mask (`00 -> 3`, all other occupancy states -> `0`).

`row_policy=densest` then performs a second, global step: count positive mask
cells per row, find the maximum, and retain mask cells only on rows attaining
that maximum.  Thus the second step cannot be evaluated cell-by-cell from the
input; it consumes the full intermediate NOR mask.

Episode inputs are setting-blind and paired.  The sampler rotates four row-count
profiles: unique maxima of three and two, plus tied maxima of two and three,
always with a lower positive row.  The minimum three-demo lesson therefore
refutes exact-three, fixed-threshold, and single-winner tie shortcuts while every
demo still separates the two declared programs.  Four-query qualification
includes a 30x7 input and 30x3 output stress case; width 7 is structural for this
source family, so a square 30x30 input is not lawful.
