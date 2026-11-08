# generic_dense_select_gen2

gen2: KEEP ONLY THE SOLID SQUARES, erase every non-square object.

Transform: among the same-color 4-connected components on a dense field, keep
those whose cells form a solid N×N block (`square?`) and erase the cells of
every other shape. The input plants a mix of solid 2×2 / 3×3 squares and
irregular non-square blobs of varied colors; the output keeps only the squares.

Selection concept: keep the objects satisfying a shape predicate.

Kind: `generic`. Imported version: `1.2.0`.
Approval is derived by the catalog from current code and retained evidence.
