# Post-repair visible-only solve

## Exposure declaration

I previously read this task's generator and canonical rule while repairing it.
This is therefore an exposed post-repair solve. During this solve phase I used
only the public challenge and my own Python code. I did not reopen the generator,
Racket rule, prior solution explanations, or private query labels. These notes
are an assistant-authored work log, not token-level training traces.

## Observation and revision 1

Visible example 0: input 3x3, output 9x9. Its three zero coordinates select three
large blocks, each containing the same three-cell zero pattern painted in 7.
Visible example 1: input 3x3, output 9x9. Four zeros select four repeated stencils,
yielding sixteen painted cells. Example 2: input 4x4, output 16x16; five zeros
produce twenty-five painted cells and distinguish a fixed-9x9 rule.

The hypothesis is the Cartesian product of the zero-coordinate set with itself:
combine an outer block coordinate and inner stencil coordinate. I implemented
this directly using two loops over zero positions. This construction creates
fresh rows and never mutates the input.

The public queries are 5x5 and 3x3. Their output dimensions and correctness were
not obtained from hidden labels; the candidate predicts them by the inferred
size rule. No deliberate negative or fictitious revision was created.
