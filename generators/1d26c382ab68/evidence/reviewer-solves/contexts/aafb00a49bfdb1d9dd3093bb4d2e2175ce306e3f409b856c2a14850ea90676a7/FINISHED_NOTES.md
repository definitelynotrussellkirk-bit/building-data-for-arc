# Solve work log

Earlier exposure: **yes**. Before this visible-only solve I had reviewed the assigned generator and its semantic contract, so this is not a blind inference record. During this solve I did not reopen the generator, Racket rule, canonical data, reference solutions, private labels, or prior solution explanations.

## Revision 1

Visible examples all contain a full maroon separator row. Above it is one connected template object; below it are three connected same-color objects with the same number of cells. Exactly one lower object has the same shape as the upper template after a rigid 0/90/180/270-degree rotation, and the output changes only that component to red (2). Reflected and merely same-size objects remain unchanged.

Implementation plan: locate the full color-9 row, extract 4-neighbor components on each side, normalize component coordinates, enumerate the upper template's four rotations, find the unique matching lower component, and recolor that component to 2 while preserving every other cell. This is translation-invariant and does not use candidate position or color as a shortcut.

Remaining uncertainty before checking: the visible examples imply exactly one template and one rotational match; the code rejects malformed/ambiguous scenes rather than guessing.

Check result: revision 1 executed successfully and matched all 3/3 visible outputs. No revision was needed. I stopped because the component-and-rotation rule accounts for every visible changed and unchanged object without a positional shortcut; private query correctness remains intentionally withheld.
