(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((opp (lambda (v) (if (= v 2) 5 2))))
             (reduce (lambda (grid r)
                       (reduce (lambda (g2 c)
                                 (if (zero? r)
                                     g2
                                     (let* ((lp (if (> c 0) (at g2 (- r 1) (- c 1)) 7))
                                            (rp (if (< c (- w 1))
                                                    (at g2 (- r 1) (+ c 1))
                                                    7)))
                                       (if (or (= lp 7) (= rp 7))
                                           g2
                                           (if (= lp rp)
                                               (set-cell g2 r c (opp lp))
                                               (set-cell g2 r c lp))))))
                               grid
                               (range 0 w)))
                     g
                     (range 0 h))))))