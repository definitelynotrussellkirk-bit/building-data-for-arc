# 703a842c8e24 — header-driven cyclic row rotation

Each row's first cell is a nonzero shift header. Keep that header fixed and cyclically rotate the remaining row body to the right by `header mod body_width`.

The version-3 generator has three exact axes (`grid_h`, `grid_w`, `n_body_colors`) and a linked four-profile curriculum:

- `canonical`: exact 4x9 public-task morphology;
- `wraparound`: large headers with visible cyclic wrap;
- `mixed_modulo`: modulo-identity plus changing rows;
- `dense_scattered`: separated/dense bodies and row-local shifts.

It includes strict canonical recognition, a Python rule mirror, executable rivals and witnesses, four-example lesson identifiability, unknown-override rejection, and task-local regression tests.

Final evidence: 11/11 focused tests and 12/12 after-battery stages green; 120/120 Racket mirror parity; 19,800/19,800 strict override draws accepted; 4/4 semantic rival claims verified; 12/12 generated lessons identifiable.
