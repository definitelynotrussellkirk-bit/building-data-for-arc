# generic_dense_recolor_gen1

gen1: per-object recolor by SIZE EXTREMES.

Transform: among the objects on the field, the UNIQUE largest one becomes
colour BIG, the UNIQUE smallest one becomes colour SMALL, and every other
object becomes colour MID. Input objects all share ONE neutral colour, so
the output reads as "rank the blobs by area, paint the extremes".

Racket: pick-max / pick-min over obj-size locate the extremes (object
identity via eq?); foldl + recolor-cells repaints each object's cells.

Object sizes are drawn DISTINCT so the max and min are unambiguous (a
prerequisite for pick-max/pick-min == the Python `size==max/min` test).

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
