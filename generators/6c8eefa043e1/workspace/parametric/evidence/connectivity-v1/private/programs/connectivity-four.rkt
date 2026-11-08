(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let ((colored (for*/list ((r (range 0 (rows g))) (c (range 0 (cols g)))
                              #:when
                              (let ((v (at g r c))) (and (!= v 0) (!= v 5))))
                            (list r c (at g r c)))))
             (let loop
                  ((grid g) (seeds colored))
                  (cond
                    ((null? seeds) grid)
                    (else (let* ((seed (car seeds))
                                 (sr (first seed))
                                 (sc (second seed))
                                 (clr (third seed))
                                 (g2 (set-cell grid sr sc 0))
                                 (g3 (flood-fill g2 sr sc clr)))
                            (loop g3 (cdr seeds))))))))))
