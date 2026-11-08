(rule!
  (for*/fold ([out g])
             ([c (in-range (cols g))]
              [r (in-range (rows g))])
    (let ((v (at g 0 c)))
      (if (not (= v 0)) (set-cell out r c v) out))))
