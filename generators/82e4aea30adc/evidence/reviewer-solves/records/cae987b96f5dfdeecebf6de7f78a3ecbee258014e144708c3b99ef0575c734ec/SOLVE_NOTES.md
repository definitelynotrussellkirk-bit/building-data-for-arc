# Solve work log

Earlier exposure before this solve: none known. I did not inspect this task's
Racket rule, generator, reference solutions, private labels, prior solution
notes, or the assigned repair generator before finishing the blind episode.

## Revision 1 — enclosed background components

Visible examples contain hollow, single-color rectangular frames on a zero
background. The output preserves every frame and changes only the zero cells
fully enclosed by a frame. A one-cell cavity becomes color 5; cavities with two
or more cells become color 7. This explains the 3×3 frames (one interior cell),
the 3×5 frame (three interior cells), the 4×3 frame (two), and the 5×3 frame
(three).

I implemented the rule without assuming a particular frame color or rectangle
orientation: find each 4-connected zero component, leave it unchanged when it
touches the grid boundary, and otherwise recolor the whole component according
to its size. This also avoids accidentally treating the exterior background as
a hole.

Before implementation I ran a visible-example regression script against the
stub and observed the expected `NotImplementedError`. After implementation the
same script passed all three visible examples. Remaining uncertainty: the
examples do not distinguish whether color 7 means specifically a non-singleton
cavity or some unobserved geometric category, but component size is the simplest
rule consistent with every visible case.
