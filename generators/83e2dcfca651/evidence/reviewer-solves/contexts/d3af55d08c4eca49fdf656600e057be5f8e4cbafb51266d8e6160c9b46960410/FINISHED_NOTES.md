# Solve work log

## Exposure declaration before revision 1

I had already inspected the selected generator and its Racket-authority summary while repairing it, so this is an exposed post-repair solve, not a blind solve. During this solve episode I used only the public `solve/README.md` / `challenge.json` presentation and did not reopen the generator, Racket rule, canonical answers, or private query labels.

## Revision 1

**Visible pattern.** Every input has one blue cell (1), one red cell (2), and one connected green object (3). The output preserves the input and adds a red copy of the entire green object. The copy displacement is the signed vector from the blue marker to the existing red marker.

The four demonstrations exercise down-right, down-left, up-right, and up-left motion, so taking absolute offsets is ruled out. The object is copied without recoloring or erasing its original cells; only the new copy is color 2.

**Implementation.** Locate the unique blue and red markers, compute `(dr, dc) = red - blue`, clone the grid, and paint every translated green cell red. I retained a bounds guard as defensive behavior, although every visible demonstration places the full translated object in bounds.

**Remaining uncertainty.** None material for the presented task. The visible examples establish the sign convention and preservation behavior directly.
