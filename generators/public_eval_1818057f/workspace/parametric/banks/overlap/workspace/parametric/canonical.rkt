(rule!
 ;; Detect every complete five-cell yellow plus on the original grid.
 ;; Diagonal cells and longer arms do not disqualify a match. Overlapping
 ;; matches are simultaneous: recolor the union of their footprints cyan.
 (lambda (g)
  (let ()
   (define offsets (cons (list 0 0) cardinal-deltas))
   (define centers
    (filter (lambda (p)
     (for/and ((d offsets))
      (= (safe-at g (+ (first p) (first d)) (+ (second p) (second d)) -1) 4)))
     (grid-positions g)))
   (for/fold ((out g)) ((p centers))
    (for/fold ((acc out)) ((d offsets))
     (set-cell acc (+ (first p) (first d)) (+ (second p) (second d)) 8))))))
