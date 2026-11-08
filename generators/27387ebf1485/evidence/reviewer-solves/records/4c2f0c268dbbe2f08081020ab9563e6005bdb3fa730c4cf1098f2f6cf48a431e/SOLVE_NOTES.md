# Solve work log

## Exposure

Before this solve I had only read the packet-level directions and the visible presentation produced by `blind prepare`. I did not open this task's generator, Racket rule, private labels, reference solutions, audit records, or prior solve explanations.

## Revision 1 — top-left key selects a crop

The cell at `(0, 0)` is a singleton whose color recurs elsewhere. In every visible example, removing that singleton and taking the tight bounding box of every remaining cell of the same color gives the output dimensions. The output is the unmodified input subgrid in that box, not a binary mask: train example 1 retains the color-8 cell enclosed by the selected color's bounds.

I considered cropping only the largest connected component. Train example 1 argues against that: several separated color-5 cells all help determine the shown 4×4 crop. The implementation therefore uses all occurrences of the top-left color except the key cell itself.

A local visible-example test was written before the solver. It failed on the placeholder `NotImplementedError`, then passed after implementing the crop. Remaining uncertainty is the second query, where the selected color occurs in two separated vertical fragments; the visible rule predicts one wide bounding box containing both fragments.
