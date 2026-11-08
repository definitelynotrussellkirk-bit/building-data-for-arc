# Solve work log

Earlier exposure: yes. Before this solve I had already reviewed the task family and repaired its generator, so this is not an independent first encounter. During this solve I kept the Racket rule, generator source, reference solutions, private labels, and earlier solution notes closed and used only the newly prepared visible examples.

## Revision 1

Hypothesis: color 4 marks the four corners of one or more axis-aligned rectangles. Copy the input and paint every strict rectangle interior with color 2. Rectangle rows and columns need not be adjacent; this matters in the second visible example, where the two rectangles' row intervals interleave. Extra color-4 cells that do not complete four corners should remain unchanged.

Implementation: collect yellow columns per row, examine every pair of yellow-bearing rows, and for every pair of shared yellow columns with nonempty interior, paint the strict Cartesian interior red. Preserve all original nonzero cells.

Visible checks expected: example 0 paints one center cell; example 2 paints a 3x3 interior; example 1 detects both interleaved rectangles rather than pairing only adjacent yellow-bearing rows. Remaining uncertainty is limited to accidental four-corner combinations, which the visible examples do not contain; the most literal inferred rule is to fill every valid rectangle.
