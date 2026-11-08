# Solve notes

This is an exposed post-repair solve: I had already inspected and repaired the task's generator and rule before this episode. During this solve I used only the newly prepared visible examples; I did not reopen the generator, Racket source, reference solutions, or private labels.

## Hypothesis

The zero rows and columns at indices 0, 6, 12, and 18 divide the grid into nine 5×5 panels. The output preserves every complete panel but permutes the panel positions. Within each source panel, one nonzero color is the shared background and the other is a marker pattern. The arithmetic centroid of all marker cells chooses the destination cell in the 3×3 panel array: mean coordinate below 1.5 maps to bucket 0, at most 2.5 to bucket 1, otherwise bucket 2.

The examples support whole-panel transport: pixel counts are unchanged, separator lines stay fixed, and each output panel can be matched exactly to one input panel. I implemented the centroid-to-destination mapping and copied each 5×5 panel without modifying it.
