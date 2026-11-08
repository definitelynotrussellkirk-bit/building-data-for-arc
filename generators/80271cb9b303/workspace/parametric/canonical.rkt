(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g)))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (let ((right (find-first (lambda (cc)
                                                      (!= 0 (at g r (- (- w 1) cc))))
                                                    (range 0 w))))
                             (if (not right)
                                 0
                                 (let ((R (- (- w 1) right)))
                                   (let ((period (find-first (lambda (p)
                                                               (for/and ((cc (range 0
                                                                                    (+ R
                                                                                       1))))
                                                                        (= (at g r cc)
                                                                           (at g
                                                                               r
                                                                               (mod cc
                                                                                    p)))))
                                                             (range 1 (+ R 2)))))
                                     (if period (at g r (mod c period)) 0))))))))))