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
                                            (start (if (zero? i)
                                                       0
                                                       (+ (nth marks (- i 1)) 1)))
                                            (color (at g r c)))
                                       (reduce (lambda (aa rr) (set-cell aa rr c color))
                                               a
                                               (range start (+ r 1)))))
                                   acc
                                   (range 0 (length marks))))))
                   g
                   (range 0 w)))))
