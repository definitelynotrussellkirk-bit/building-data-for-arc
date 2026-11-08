(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (period (find-first (lambda (p)
                                      (for/and ((r (range 0 h)))
                                               (= (row-at g r) (row-at g (mod r p)))))
                                    (range 1 (+ h 1))))
                (new-h (+ h (floor (/ h 3)))))
           (grid-from-fn new-h
                         w
                         (lambda (r c)
                           (let* ((v (at g (mod r period) c))) (if (= v 1) 2 v)))))))