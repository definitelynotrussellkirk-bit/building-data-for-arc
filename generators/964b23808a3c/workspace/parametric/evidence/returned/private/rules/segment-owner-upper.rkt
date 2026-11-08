(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (reduce (lambda (acc c)
                     (let* ((marks (filter (lambda (r) (!= (at g r c) 0)) (range 0 h))))
                       (if (or
                             (empty? marks)
                             (!= (at g (nth marks (- (length marks) 1)) c) 5))
                           acc
                           (reduce (lambda (a i)
                                     (let* ((r (nth marks i))
                                            (previous-row (if (zero? i)
                                                              -1
                                                              (nth marks (- i 1))))
                                            (start (+ previous-row 1))
                                            (end (if (zero? i) (+ r 1) r))
                                            (color (if (zero? i)
                                                       (at g r c)
                                                       (at g previous-row c))))
                                       (reduce (lambda (aa rr) (set-cell aa rr c color))
                                               a
                                               (range start end))))
                                   acc
                                   (range 0 (length marks))))))
                   g
                   (range 0 w)))))
