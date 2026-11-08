# Solve work log

## Prior exposure

Before this visible-only solve was prepared, I had already inspected the assigned generator and canonical rule while repairing it. I therefore will finish with `--earlier-exposure yes`. During this solve phase I did not reopen the generator, Racket rule, reference solutions, private labels, or prior solution explanations; I used only the newly prepared visible examples and my own code.

## Revision 1

**Visible pattern.** In every training pair, color-2 cells form two or more spatially separated 4-connected components. Each component is replaced by a solid color-3 rectangle spanning exactly its minimum and maximum occupied rows and columns. The original red cells are recolored, background cells inside the rectangle are filled, and unrelated cells of colors 5, 7, 8, or 9 remain unchanged.

**Alternatives considered.** A single global rectangle around all red cells is contradicted by the large untouched gaps between components. A fixed 3x2 rectangle per object is contradicted by training examples whose component closure is 3x3. Merely adding green while retaining red is contradicted by every output.

**Implementation.** Scan the grid, find each 4-connected color-2 component with breadth-first search, compute its bounding box, and paint that complete box color 3 in a copied grid. Other colors are preserved unless they lie inside such a box; the visible examples place decorations outside the boxes, so no extra precedence rule is needed.

**Remaining uncertainty.** The examples do not show a non-red decoration inside a red component's bounding box. The simplest supported transformation paints the complete box, so the implementation would overwrite such a cell. All visible examples should be exact under this rule.
