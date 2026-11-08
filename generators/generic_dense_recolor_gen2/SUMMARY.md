# generic_dense_recolor_gen2

gen2: per-object recolor by SHAPE CLASS.

Transform: each object is repainted by what KIND of shape it is —
  - a solid square (N x N filled)        -> colour SQ
  - a straight line (1 row or 1 column)  -> colour LN
  - anything else (rectangles, L/T/blobs)-> colour OT
Input objects all share ONE neutral colour, so the rule is "sort the
blobs into square / line / other and colour by class".

Racket: foldl over (objects g); per object a cond on (square? o),
(or (hline? o) (vline? o)), else; recolor-cells repaints the cells.
Classification is per-object and order-independent.

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
