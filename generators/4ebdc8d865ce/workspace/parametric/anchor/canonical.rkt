(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g)))
           (map-grid g
                     (lambda (r c v)
                       (if (!= v 2)
                           v
                           (if (or
                                 (and (> r 0) (= 2 (at g (- r 1) c)))
                                 (and (< r (- h 1)) (= 2 (at g (+ r 1) c)))
                                 (and (> c 0) (= 2 (at g r (- c 1))))
                                 (and (< c (- w 1)) (= 2 (at g r (+ c 1)))))
                               2
                               1)))))))