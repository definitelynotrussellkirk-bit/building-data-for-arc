(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (if (!= 5 v)
                        v
                        (let ((l (if (and (> c 0) (= 5 (at g r (- c 1)))) 1 0))
                              (ri (if (and (< c (- (cols g) 1)) (= 5 (at g r (+ c 1))))
                                      1
                                      0))
                              (u (if (and (> r 0) (= 5 (at g (- r 1) c))) 1 0))
                              (d (if (and (< r (- (rows g) 1)) (= 5 (at g (+ r 1) c)))
                                     1
                                     0)))
                          (if (>= (+ l ri u d) 3) 2 5)))))))