(rule!
  (for*/fold ([out g])
             ([r (in-range (rows g))]
              [c (in-range (- (cols g) 1))])
    (if (and (= (at g r c) 4) (= (at g r (+ c 1)) 4))
        (let* ((left-out (if (and (>= (- c 1) 0) (= (at g r (- c 1)) 0))
                             (set-cell out r (- c 1) 9)
                             out))
               (right-c (+ c 2)))
          (if (and (< right-c (cols g)) (= (at g r right-c) 0))
              (set-cell left-out r right-c 9)
              left-out))
        out)))
