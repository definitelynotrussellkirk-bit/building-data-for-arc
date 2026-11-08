(rule!
  (for*/fold ([out (empty-grid (rows g) (cols g) 0)])
             ([r (in-range (rows g))]
              [c (in-range (cols g))])
    (let ((v (at g r c)))
      (if (and (not (= v 0))
               (any? (lambda (d)
                       (let ((nr (+ r (first d))) (nc (+ c (second d))))
                         (and (in-bounds? nr nc (rows g) (cols g))
                              (= (at g nr nc) v))))
                     cardinal-deltas))
          (set-cell out r c v)
          out))))