(rule! (lambda (g)
         (let ((h (rows g))
               (w (cols g)))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (let ((v (at g r c)))
                             (if (or
                                   (>= (+ (if (= 4 (at g r 0)) 1 0) (if (= 4 (at g r (- w 1))) 1 0)) 1)
                                   (>= (+ (if (= 4 (at g 0 c)) 1 0) (if (= 4 (at g (- h 1) c)) 1 0)) 1))
                                 (cond
                                   ((zero? v) 8)
                                   ((= v 8) 0)
                                   ((= v 6) 7)
                                   ((= v 7) 6)
                                   (else v))
                                 v)))))))