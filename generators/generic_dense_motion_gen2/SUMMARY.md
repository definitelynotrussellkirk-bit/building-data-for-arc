# generic_dense_motion_gen2

gen2: slide every object to a wall — direction FIXED per task, varying across
seeds (one of up / down / left / right). Whole-object `move-to-wall`, shape
preserved (NOT per-cell gravity).

Layout adapts to the motion axis so objects never collide:
  - up / down   -> DISJOINT COLUMN LANES (no two objects share a column)
  - left / right-> DISJOINT ROW LANES    (no two objects share a row)
Component count is therefore preserved exactly.

Program (one rule, shared by all pairs; DIR is the per-task direction):
    (let ([objs (objects g)])
      (foldl (lambda (o acc) (move-to-wall acc (obj-cells o) 'DIR)) g objs))

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
