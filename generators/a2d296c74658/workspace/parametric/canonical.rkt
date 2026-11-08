(rule!
  (for*/fold ([out g])
             ([r (in-range 1 (- (rows g) 1))]
              [c (in-range (cols g))])
    (if (and (= (at g r c) 0)
             (= (at g (- r 1) c) 7)
             (= (at g (+ r 1) c) 7))
        (set-cell out r c 4)
        out)))