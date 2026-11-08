# generic_dense_motion_gen3

gen3: magnetism to a central bar. A full-height WALL line (one fixed color)
splits the grid; every object slides HORIZONTALLY toward the wall until it is
flush against it (whole-object `slide-until-contact`, shape preserved).

Layout: objects live in DISJOINT ROW LANES (no two share a row) and each sits
entirely on one side of the wall with a >=1 column gap. Direction per object is
derived in the rule from its side of the wall, so objects on the left slide
right and objects on the right slide left. The wall is a single component; the
object count + 1 (the wall) is preserved exactly.

Program (one rule, shared by all pairs; W is the wall color, B is background):
    (let* ([wallcol (for/first ([c (in-range (cols g))]
                       #:when (andmap (lambda (r) (= (cell-at g r c) W))
                                      (range 0 (rows g)))) c)]
           [wall-cells (for/list ([r (in-range (rows g))]) (list r wallcol))]
           [objs (filter (lambda (o) (not (= (obj-color o) W))) (objects g B))])
      (foldl (lambda (o acc)
               (let ([dir (if (< (second (obj-bbox o)) wallcol) 'right 'left)])
                 (slide-until-contact acc (obj-cells o) wall-cells dir B)))
             g objs))

Kind: `generic`. Imported version: `1.1.0`.
Approval is derived by the catalog from current code and retained evidence.
