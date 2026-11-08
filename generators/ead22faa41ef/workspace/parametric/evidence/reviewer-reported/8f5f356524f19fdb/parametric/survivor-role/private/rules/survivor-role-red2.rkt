(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g)))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (let ((v (at g r c)))
                             (cond
                               ((and
                                  (= v 3)
                                  (or
                                    (and (> r 0) (= 2 (at g (- r 1) c)))
                                    (and (< r (- h 1)) (= 2 (at g (+ r 1) c)))
                                    (and (> c 0) (= 2 (at g r (- c 1))))
                                    (and (< c (- w 1)) (= 2 (at g r (+ c 1)))))) 0)
                               ((and
                                  (= v 2)
                                  (or
                                    (and (> r 0) (= 3 (at g (- r 1) c)))
                                    (and (< r (- h 1)) (= 3 (at g (+ r 1) c)))
                                    (and (> c 0) (= 3 (at g r (- c 1))))
                                    (and (< c (- w 1)) (= 3 (at g r (+ c 1)))))) 8)
                               (else v))))))))