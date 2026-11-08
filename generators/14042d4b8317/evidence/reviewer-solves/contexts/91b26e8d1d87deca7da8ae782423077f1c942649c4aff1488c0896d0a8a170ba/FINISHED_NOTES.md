# Solve work log

Earlier exposure: none. Before this solve I had not opened task `14042d4b8317`'s generator, rule, notes, solutions, audits, or private labels. I used only `solve-blind/challenge.json` and the packet's solve instructions.

## Revision 1 — complete the missing rectangle corner

In every visible training pair, the nonzero cells of one colour occupy exactly three corners of an axis-aligned rectangle:

- `(10,8), (10,11), (11,11)` gains `(11,8)`;
- `(1,2), (1,5), (4,2)` gains `(4,5)`;
- `(8,14), (8,16), (12,16)` gains `(12,14)`.

The output preserves all existing cells and adds the fourth Cartesian-product point of the two occupied row coordinates and two occupied column coordinates. The second query contains two independent colours, so the operation should be applied separately to each nonzero colour.

Implementation: group nonzero coordinates by colour; for a group of three cells spanning exactly two rows and two columns, fill its unique missing corner. I deliberately avoid connecting lines or filling the rectangle interior because the examples add only one cell. Remaining uncertainty is limited to unshown cases with more than one rectangle of the same colour; the visible task gives no evidence for partitioning such a group.
