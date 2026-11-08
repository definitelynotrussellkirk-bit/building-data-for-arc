# Post-repair solve work log

Earlier rule exposure: yes. Reference consulted during this solve: no.

The visible examples are all 5×29 strips: five 5-column panels separated by one blank column, with 5×5 outputs. Foreground colors change both within and across examples, while the output relations remain symmetric, so color is not the key.

Hypothesis frozen for revision 1: crop each panel to its nonzero bounding box, binarize its support, then compare pairwise. Diagonal is 8; exact normalized shape is 1; a rotation is 2; a reflected rotation is 3; otherwise 0. The ordering matters because identity is also in every transform orbit.

Implementation is independent from the generator source: it extracts panels from the visible strip, normalizes occupied coordinates, enumerates four rotations and the full eight-element dihedral family, and emits the relation matrix.
