(rule!
  (for*/fold ([out g])
             ([r (in-range 1 (- (rows g) 1))]
              [c (in-range 1 (- (cols g) 1))])
    (let ((vals (list (at g (- r 1) c) (at g (+ r 1) c) (at g r (- c 1)) (at g r (+ c 1)))))
      (if (and (= (at g r c) 0)
               (not (= (first vals) 0))
               (all? (lambda (v) (= v (first vals))) vals))
          (set-cell out r c (first vals))
          out))))