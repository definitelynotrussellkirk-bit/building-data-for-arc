# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private
labels, prior solve notes, or any repair target. I used only the visible examples
printed by `python3 review.py blind prepare` and the generated public README.

## Revision 1 — classify disconnected gray objects by area

All three training inputs contain exactly fourteen gray cells partitioned into
three 4-connected objects. Their shapes and positions vary, but their areas are
always 3, 5, and 6. The output preserves every occupied coordinate and changes
only the object color:

- area 3 becomes red (2),
- area 5 becomes yellow (4),
- area 6 becomes blue (1).

This explains every changed cell in all three examples. It also distinguishes
objects by a property invariant under translation, rotation, reflection, and
shape changes. I considered alternatives based on orientation, bounding-box
shape, or scan order, but those conflict across the examples: the same output
color appears on horizontal, vertical, and bent objects in different positions.

I implemented a 4-neighbor flood fill over gray (5) cells, counted each
component, and recolored it with the observed size map. Unknown component sizes
are conservatively left gray rather than guessed. Both test inputs visibly split
into the same three areas, so no extrapolation beyond the demonstrated sizes is
needed. Remaining uncertainty is limited to whether diagonal touching should
connect objects; the examples consistently support 4-connectivity, and no query
contains a diagonal ambiguity.
