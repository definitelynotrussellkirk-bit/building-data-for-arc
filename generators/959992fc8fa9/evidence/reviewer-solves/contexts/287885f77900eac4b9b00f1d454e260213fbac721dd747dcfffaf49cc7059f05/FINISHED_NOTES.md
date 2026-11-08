# Solve work log

## Prior exposure

I had not opened this task's generator, rule, notes, reference solution, private
labels, or earlier solution explanations before solving.  I had only seen the
three visible training pairs and two visible queries produced by `blind prepare`.

## Revision 1 — row/column rays with red mixed-color crossings

Each nonzero input cell behaves as a colored marker.  Its color is copied across
its complete row and complete column.  At a cell reached by lines of one distinct
color, the output has that color.  At a crossing reached by different colors,
the output is red (`2`).  Intersections of two lines with the same color stay
that color, as shown by the two `3` markers in training example 1.

I implemented the rule by collecting the set of marker colors in every input row
and column, then taking the union of the corresponding row and column sets for
each output cell.  Empty union gives `0`, one color gives that color, and two or
more distinct colors give `2`.  This also provides a deterministic interpretation
for a marker crossed by a differently colored line, though the visible examples
do not exercise that case.

Remaining uncertainty: the examples appear to keep markers in distinct rows and
columns, so they do not distinguish whether an original marker would be protected
from a differently colored crossing.  The uniform mixed-color-intersection rule
is the simplest extension of all visible evidence.
