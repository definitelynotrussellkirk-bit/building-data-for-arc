(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((pixels (for*/list ((r (range 0 h)) (c (range 0 w)) #:when (!= (at g r c) 0))
                            (list r c (at g r c)))))
             (cellmap g
                      (r c v)
                      (let loop
                           ((ps pixels))
                           (cond
                             ((null? ps) 0)
                             (else (let* ((p (car ps))
                                          (pr (first p))
                                          (pc (second p))
                                          (col (third p))
                                          (go-up (>= (* 2 pr) (- h 1)))
                                          (go-left (>= (* 2 pc) (- w 1)))
                                          (on-v (and
                                                  (= c pc)
                                                  (if go-up
                                                      (and (>= r 0) (<= r pr))
                                                      (and (>= r pr) (<= r (- h 1))))))
                                          (on-h (and
                                                  (= r pr)
                                                  (if go-left
                                                      (and (>= c 0) (<= c pc))
                                                      (and (>= c pc) (<= c (- w 1)))))))
                                     (if (or on-v on-h) col (loop (cdr ps))))))))))))
