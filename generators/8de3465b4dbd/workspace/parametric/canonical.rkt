(rule!
  (for*/fold ([out g])
             ([r (in-range (rows g))]
              [c (in-range (- (cols g) 2))])
    (if (and (= (at g r c) 2) (= (at g r (+ c 1)) 3) (= (at g r (+ c 2)) 0))
        (set-cell out r (+ c 2) 8)
        out)))