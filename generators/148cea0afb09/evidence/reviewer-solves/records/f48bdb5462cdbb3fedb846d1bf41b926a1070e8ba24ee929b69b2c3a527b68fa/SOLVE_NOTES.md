# Solve work log

## Exposure record

Earlier rule exposure is **yes** because I reviewed this generator before the final source-bound solve. After `prepare` produced this final episode, I did not reopen the generator, Racket source, reference solution, prior solve notes, or private query labels. I used only the visible examples in `solve/README.md` and visible-check feedback.

## Revision 1

The top-left nonzero cell is a small integer marker, while the remaining nonzero cells form separated objects of one color. The visible pairs support this rule:

1. Save the top-left value as a one-based rank and erase that marker.
2. Find the 4-connected nonzero objects.
3. Sort objects by occupied-cell count, ascending, and select the indicated rank.
4. Crop that object to its tight bounding box, keeping background holes.
5. Expand every crop cell into a 2×2 block.

The examples separate relative cell-count ranking from position and bounding-box size. They also show that a selected object may be a solid rectangle, so no non-rectangularity condition belongs in the rule. The only unresolved cases are undeclared ties or malformed rank markers; the visible examples have unique object sizes and valid ranks.
