# Visible-only solve notes

The four inputs are laid out as four width-5 panels separated by blank columns
5, 11, and 17. Each output is a 4x4 symmetric relation matrix with cyan on the
diagonal. Comparing the visible examples shows that two off-diagonal cells are
cyan exactly when the cropped occupied shapes in the corresponding panels agree
under a quarter-turn rotation; object colors and absolute offsets do not matter.

Implementation: extract nonzero coordinates from each panel, normalize by its
bounding-box origin, compute a canonical key over its four rotations, then emit
8 when two keys match and 0 otherwise.

This was the first implementation. I had seen the task rule earlier during the
generator review, so this is an exposed solve even though the implementation and
check used only the visible challenge during this solve phase.
