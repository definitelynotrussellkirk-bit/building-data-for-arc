(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (grid-from-fn h
                         w
                         (lambda (r c)
                           (if (= r 0)
                               (if (for/or ((rr (range 0 h))) (= 1 (at g rr c)))
                                   1
                                   (at g r c))
                               (if (= 1 (at g r c)) 0 (at g r c))))))))