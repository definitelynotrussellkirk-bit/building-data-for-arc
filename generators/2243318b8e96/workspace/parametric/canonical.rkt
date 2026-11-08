(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([obj (objects g 0)])
    (paint-cells out (obj-cells obj) (if (= (modulo (obj-size obj) 2) 1) 3 8))))
