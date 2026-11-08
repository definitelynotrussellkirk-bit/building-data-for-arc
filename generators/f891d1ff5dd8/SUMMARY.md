# f891d1ff5dd8

Rows 0 and 1 are preserved. Row 0 is an ordered positional color cycle; every
row from index 2 onward is overwritten with one solid color selected by
`row0[(row - 2) % width]`.

Reviewed generator version: `2.1.0`. The ordinary four-slot curriculum is:

1. exact canonical-size/palette anchor with a blank body;
2. all-distinct header with a nonzero body rectangle and more than two complete
   header cycles, refuting fill-only and two-cycles-only;
3. repeated positional header with a blank body, refuting deduplicated cycles;
4. repeated positional header with a body rectangle and more than two complete
   header cycles, combining all three counterexamples.

Every three consecutive slots, including every single-pair query rotation,
contains witnesses against all three declared canonical-fitting shortcuts:
preserve body decoys, deduplicate repeated header colors, and stop after exactly
two header cycles. Public exact controls are limited to
`grid_h`, `grid_w`, and `body_pattern`; all are exact, observable, and loud on
invalid or unknown values. The generator pins canonical rule hash
`9a77eb6a5412` and validates a compact blank-or-rectangle input grammar.

A separate unapproved task-local prototype under `workspace/parametric/` varies
`cycle_direction` between canonical `forward` and proposed `reverse`, selecting
one setting per episode and deriving all labels with exact Racket execution.

Kind: `per_puzzle`. Approval is derived by the catalog from current code and
retained evidence; this review does not itself admit generated lessons to
training.
