(rule! (lambda (grid)
  (define all-objects (objects grid 0))
  (define (largest-of color)
    (first
      (sort
        (filter (lambda (obj) (= (obj-color obj) color)) all-objects)
        (lambda (a b) (> (obj-size a) (obj-size b))))))
  (let* ((largest-red (largest-of 2))
         (largest-green (largest-of 3))
         (blank (empty-grid (rows grid) (cols grid) 0)))
    (recolor-cells
      (recolor-cells blank (obj-cells largest-red) 4)
      (obj-cells largest-green) 1))))