# Solve work log

## Exposure declaration

Before this solve I had not opened task `483682b75e12`'s generator, rule, notes,
solutions, audit records, or private labels. I used only the public examples
printed by `solve_episode.py blind prepare` and the visible solve files.

## Revision 1 — object area controls jump distance

Observed that the uniform color-8 bottom row remains fixed and the dominant
color-7 field remains background. Every other monochrome connected object keeps
its shape and column, but moves upward. The displacement equals the object's
cell count: the 3-cell bars move 3 rows, the 4-cell T moves 4, the 2-cell bar
moves 2, and the singleton moves 1. Objects move simultaneously rather than
stacking or falling.

Implemented a generic solver that detects a solid non-background edge, finds
same-color 4-connected components away from it, clears them, then translates
each component away from the edge by its area. I generalized the direction to
all four edges, although only a bottom floor is demonstrated. Remaining
uncertainty: the public examples do not show diagonal connectivity, repeated
same-color disconnected objects, collisions, or an object whose jump would
leave the grid; the generator appears to avoid those cases.
