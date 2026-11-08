(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (objects g 0)])
    (draw-rect-outline out (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj) (obj-color obj))))