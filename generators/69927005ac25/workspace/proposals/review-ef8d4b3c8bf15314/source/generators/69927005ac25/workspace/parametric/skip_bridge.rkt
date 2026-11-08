(rule!
  (for*/fold ([out g])
             ([r (in-range (- (rows g) 2))]
              [c (in-range (cols g))]
              [dc (in-list (list 1 -1))])
    (let* ((v (at g r c))
           (mc (+ c dc))
           (ec (+ c (* 2 dc))))
      (if (and (not (= v 0))
               (in-bounds? (+ r 2) ec (rows g) (cols g))
               (= (at g (+ r 1) mc) v)
               (= (at g (+ r 2) ec) v))
          (let* ((out1 (if (= (at out r ec) 0) (set-cell out r ec v) out))
                 (out2 (if (= (at out1 (+ r 2) c) 0)
                           (set-cell out1 (+ r 2) c v)
                           out1)))
            out2)
          out))))
