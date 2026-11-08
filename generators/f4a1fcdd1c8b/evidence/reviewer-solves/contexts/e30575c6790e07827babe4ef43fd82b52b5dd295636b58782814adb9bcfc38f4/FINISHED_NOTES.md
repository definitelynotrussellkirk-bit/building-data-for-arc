# Solve work log

## Exposure and source discipline

- Earlier exposure to the reference rule or this task: no known exposure.
- Sources used: only the prepared visible examples in `challenge.json` / `README.md` and local tests written from those examples.
- The generator, Racket rule, private labels, reference solutions, notes, and audit evidence remained closed.

## Revision 1 — boundary-connected objects

At first I considered whether the transformation removed duplicate shapes, because two interior tetrominoes disappear in training example 0. That explanation fails immediately: another congruent tetromino at the right edge remains. The consistent distinction across all three examples is contact with the canvas boundary.

Hypothesis: treat each same-color, nonzero, 4-connected component independently. Preserve a component exactly when at least one of its cells lies on the top, bottom, left, or right edge; replace every cell of every entirely interior component with background 0.

Visible evidence:

- Example 0 preserves the red object touching the top, orange object touching the right, and magenta object touching the bottom; it removes the blue and yellow interior objects.
- Example 1 preserves the left-border gray rectangle, right-border azure object, and bottom-border orange object. The separate interior gray component is removed, showing that the decision is per connected component rather than per color.
- Example 2 preserves the top-, right-, and bottom-touching objects and removes both interior objects.

Probe: a standard-library unit test loads every visible training pair and adds a synthetic case containing disconnected objects of the same color plus an interior component. The original skeleton failed with `NotImplementedError`; the component flood-fill implementation passes.

Remaining uncertainty: the examples establish 4-connectivity more naturally than diagonal connectivity, and all objects are monochromatic. The implementation therefore uses same-color 4-connected components and does not merge diagonal contact or different colors.
