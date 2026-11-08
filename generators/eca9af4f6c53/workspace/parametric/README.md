# Native parametric family: global color versus two local passes

`completion_mode=global_color` is the exact 623-byte canonical program: a color
is completed only when all of its cells globally form exactly three corners of
one 2x2 square.

`completion_mode=two_pass_local` is sequential. Step A simultaneously fills the
missing corner of every local monochrome 2x2 L-tromino. Step B recomputes the same
predicate on that input-dependent intermediate grid and performs one additional
pass. Every generated scene contains a two-row chain where the first pass enables
the second and the second leaves a third-pass opportunity, ruling out one-pass
and closure shortcuts.

The adapter supports 2–6 demonstrations and exactly four private queries. Inputs
are matched across settings; the fourth query is a dense 30x30 case.
