(rule!
  (let* ((bridged
          (for*/fold ([out g])
                     ([r (in-range (rows g))]
                      [c (in-range (cols g))]
                      [d (in-list (list (list 2 2) (list 2 -2)))])
            (let* ((v (at g r c))
                   (nr (+ r (first d)))
                   (nc (+ c (second d)))
                   (mr (+ r 1))
                   (mc (+ c (quotient (second d) 2))))
              (if (and (not (= v 0))
                       (in-bounds? nr nc (rows g) (cols g))
                       (= (at g nr nc) v)
                       (= (at out mr mc) 0))
                  (set-cell out mr mc v)
                  out)))))
    (for*/fold ([out bridged])
               ([r (in-range (- (rows bridged) 2))]
                [c (in-range (cols bridged))]
                [dc (in-list (list 1 -1))])
      (let* ((v (at bridged r c))
             (mc (+ c dc))
             (ec (+ c (* 2 dc))))
        (if (and (not (= v 0))
                 (in-bounds? (+ r 2) ec (rows bridged) (cols bridged))
                 (= (at bridged (+ r 1) mc) v)
                 (= (at bridged (+ r 2) ec) v))
            (let* ((out1 (if (= (at out r ec) 0) (set-cell out r ec v) out))
                   (out2 (if (= (at out1 (+ r 2) c) 0)
                             (set-cell out1 (+ r 2) c v)
                             out1)))
              out2)
            out)))))
