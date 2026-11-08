# 3020cc038f3f native parametric family

`preprocess=identity` is the exact selected canonical program.  In
`preprocess=rotate_larger_cw`, step A normalizes both colored operands and
compares their occupied areas, producing the input-dependent intermediate
`larger_color`.  Step B consumes that result by rotating only that operand
clockwise before the visible control cell chooses union, XOR, or intersection.
A wrong intermediate that names the smaller color changes the retained witness.

The sampler keeps visible inputs identical across settings, supports 2–6
prefix-stable demonstrations and 1–4 prefix-stable queries, and reserves the
fourth query for substantive 30x30 stress.  The first two demonstrations swap
which color is larger and use different controls, refuting fixed-color,
skipped-selection, wrong-rotation, bbox-area-selection, and fixed-operation
shortcuts in the declared finite audit.  `public_turn()` exposes all labeled
demonstrations and exactly one unlabeled query, with no setting, program, future
query, or answer.
