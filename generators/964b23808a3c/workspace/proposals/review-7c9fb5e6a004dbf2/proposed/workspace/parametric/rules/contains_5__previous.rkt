(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (reduce (lambda (acc c)
                     (let* ((marks (filter (lambda (r) (!= (at g r c) 0)) (range 0 h))))
                       (if (or
                             (empty? marks)
                             (empty? (filter (lambda (r) (= (at g r c) 5)) marks)))
                           acc
                           (reduce (lambda (a i)
                                     (let* ((r (nth marks i))
                                            (start (if (zero? i)
                                                       0
                                                       (+ (nth marks (- i 1)) 1)))
                                            (color (if (zero? i)
                                                       (at g r c)
                                                       (at g (nth marks (- i 1)) c)))
                                            (stop (if (zero? i)
                                                      (+ r 1)
                                                      r)))
                                       (reduce (lambda (aa rr) (set-cell aa rr c color))
                                               a
                                               (range start stop))))
                                   acc
                                   (range 0 (length marks))))))
                   g
                   (range 0 w)))))