(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((corners (filter (lambda (x) x)
                                  (flatmap (lambda (r)
                                             (map (lambda (c)
                                                    (and
                                                      (and
                                                        (= (at g r c) 3)
                                                        (or
                                                          (zero? r)
                                                          (!= (at g (- r 1) c) 3))
                                                        (or
                                                          (zero? c)
                                                          (!= (at g r (- c 1)) 3)))
                                                      (let ((rh (let loop
                                                                     ((rr 1))
                                                                     (if (and
                                                                           (< (+ r rr)
                                                                              h)
                                                                           (= (at g
                                                                                  (+ r
                                                                                     rr)
                                                                                  c)
                                                                              3))
                                                                         (loop (+ rr 1))
                                                                         rr)))
                                                            (rw (let loop
                                                                     ((cc 1))
                                                                     (if (and
                                                                           (< (+ c cc)
                                                                              w)
                                                                           (= (at g
                                                                                  r
                                                                                  (+ c
                                                                                     cc))
                                                                              3))
                                                                         (loop (+ cc 1))
                                                                         cc))))
                                                        (list r c rh rw))))
                                                  (range 0 w)))
                                           (range 0 h)))))
             (cellmap g
                      (r c v)
                      (if (or
                            (= v 3)
                            (let loop
                                 ((rs corners))
                                 (if (null? rs)
                                     #f
                                     (let* ((rect (first rs))
                                            (r0 (first rect))
                                            (c0 (second rect))
                                            (rh (third rect))
                                            (rw (fourth rect)))
                                       (if (>= (- r r0) rh)
                                           (let* ((k (quotient (- r r0) rh))
                                                  (row-in-block (modulo (- r r0) rh)))
                                             (if (let ((nc (+ c0 (* k rw))))
                                                     (and (>= c nc) (< c (+ nc rw))))
                                                 #t
                                                 (loop (rest rs))))
                                           (loop (rest rs)))))))
                          3
                          0))))))