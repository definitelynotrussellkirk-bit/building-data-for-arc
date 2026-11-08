(rule!
  (let ()
    (define pts
      (map (lambda (cell) (list (first cell) (second cell)))
           (filter (lambda (cell) (not (= (third cell) 0)))
                   (grid-cells g))))
    (define r0 (apply min (map first pts)))
    (define r1 (apply max (map first pts)))
    (define c0 (apply min (map second pts)))
    (define c1 (apply max (map second pts)))
    (define target-size
      (min (+ 1 (- r1 r0)) (+ 1 (- c1 c0))))
    (define candidates
      (filter (lambda (obj)
                (and (not (= (obj-color obj) 1))
                     (= (obj-size obj) target-size)))
              (objects g 0)))
    (define chosen (first candidates))
    (paint-cells
      (empty-grid (obj-h chosen) (obj-w chosen) 0)
      (normalize-cells (obj-cells chosen))
      8)))