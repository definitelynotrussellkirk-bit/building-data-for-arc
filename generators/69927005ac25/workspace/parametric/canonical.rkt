(rule!
  (for*/fold ([out g])
             ([r (in-range (rows g))]
              [c (in-range (cols g))]
              [d (in-list (list (list 2 2) (list 2 -2)))])
    (let* ((v (at g r c))
           (nr (+ r (first d)))
           (nc (+ c (second d)))
           (mr (+ r (quotient (first d) 2)))
           (mc (+ c (quotient (second d) 2))))
      (if (and (not (= v 0))
               (in-bounds? nr nc (rows g) (cols g))
               (= (at g nr nc) v)
               (= (at out mr mc) 0))
          (set-cell out mr mc v)
          out))))