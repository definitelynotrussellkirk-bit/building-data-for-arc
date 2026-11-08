(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (let* ((gi (reduce (lambda (acc r2)
                                         (if (all? (lambda (kc)
                                                     (= (at g r2 kc) (at g (- r2 1) kc)))
                                                   (range 0 w))
                                             acc
                                             (+ acc 1)))
                                       0
                                       (range 1 (+ r 1)))))
                      (if (and (zero? (mod gi 3)) (!= v 0)) 2 v))))))