(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (if (!= 5 v)
                        v
                        (let* ((l (if (and (> c 0) (= 5 (at g r (- c 1)))) 1 0))
                               (ri (if (and (< c (- (cols g) 1)) (= 5 (at g r (+ c 1))))
                                       1
                                       0))
                               (u (if (and (> r 0) (= 5 (at g (- r 1) c))) 1 0))
                               (d (if (and (< r (- (rows g) 1)) (= 5 (at g (+ r 1) c)))
                                      1
                                      0))
                               (h-both (and (= 1 l) (= 1 ri)))
                               (v-both (and (= 1 u) (= 1 d))))
                          (cond
                            ((and h-both v-both) 2)
                            ((and (not h-both) (not v-both)) 1)
                            (else 4))))))))