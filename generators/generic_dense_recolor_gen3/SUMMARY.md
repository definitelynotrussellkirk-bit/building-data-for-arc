# generic_dense_recolor_gen3

gen3: per-object recolor by EXACT CELL-COUNT (size -> colour map).

Transform: a fixed mapping size->colour is applied to every object —
all 4-cell objects become one colour, all 5-cell objects another, etc.
Objects of the same area end up the same colour regardless of shape or
position. Input objects share ONE neutral colour, so the rule is
"count each blob's cells and look the colour up".

Racket: foldl over (objects g); per object a cond on (obj-size o)
selecting the mapped colour; recolor-cells repaints. Order-independent.

Generation only ever uses sizes present in the map, so every object is
covered (the cond `else` is a safety fallback that is never reached).

Kind: `generic`. Imported version: `1.2.0`.
Approval is derived by the catalog from current code and retained evidence.
