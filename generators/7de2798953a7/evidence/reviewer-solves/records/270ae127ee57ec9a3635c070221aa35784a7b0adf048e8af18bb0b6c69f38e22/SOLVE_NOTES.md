# Visible-only solve work log

The three demonstrations show a row-local transformation.

Hypothesis: when a row contains exactly two nonzero cells of the same colour, keep the endpoints and copy that colour into every other interior cell, starting with the cell immediately to the right of the left endpoint. Rows with unequal endpoint colours stay unchanged. Empty rows stay unchanged.

Evidence from visible examples:
- Train 1 row with 5 at columns 2 and 6 fills columns 3 and 5, while the endpoints remain.
- Train 2 row with unequal colours 6 and 2 is unchanged, establishing that equality is required rather than merely two nonzero endpoints.
- Both odd and even endpoint separations occur, fixing the phase as left-anchored rather than right-anchored.

Implementation plan: copy the grid; for each row, collect nonzero positions; only when there are exactly two and their colours match, write the left colour at interior offsets 1, 3, 5, ... from the left endpoint.
