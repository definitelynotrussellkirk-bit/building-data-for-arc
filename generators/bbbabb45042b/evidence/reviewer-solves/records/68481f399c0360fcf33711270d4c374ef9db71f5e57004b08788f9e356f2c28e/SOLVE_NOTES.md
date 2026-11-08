# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private labels,
or prior solution notes. I used only `solve-blind/challenge.json` and local Python.

## Revision 1 — largest red component as a stamp

The visible examples contain one multi-cell red object, one or more isolated blue
markers, and in one example an unrelated isolated red cell. The output preserves the
input and adds a blue copy of the multi-cell red object at each blue marker. The marker
is the top-left corner of the red object's bounding box, not necessarily an occupied
cell of the red shape; this explains the extra blue corner in examples whose red
bounding-box corner is empty.

I considered treating all red cells as one template, but the second example's isolated
red cell would make a large sparse bounding box and contradict the output. I therefore
use the largest 4-connected red component. I preserve non-background cells rather than
overwriting them and clip defensively at grid boundaries, although every visible stamp
fits fully inside its grid.

Before implementation I ran a visible-example assertion against the initial stub and
observed the expected `NotImplementedError`. After implementation I reran the same
three visible-example comparisons.

Remaining uncertainty: the examples do not distinguish preservation from overwrite if
a stamp collides with a non-background distractor, nor do they establish a tie-break
between equally large red components. The implementation uses the first component in
row-major order after maximizing component size.
