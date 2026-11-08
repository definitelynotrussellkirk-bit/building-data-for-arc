(rule! (lambda (g)
  (let ((colored
         (for*/list ((r (range 0 (rows g)))
                     (c (range 0 (cols g)))
                     #:when
                     (let ((v (at g r c)))
                       (and (!= v 0) (!= v 5))))
           (list r c (at g r c)))))
    (letrec ((flood-8
              (lambda (grid sr sc clr)
                (let grow ((current (set-cell grid sr sc clr)))
                  (let ((next
                         (map-grid
                          current
                          (lambda (r c v)
                            (if (and (= v 0)
                                     (member clr (neighbors-8 current r c -1)))
                                clr
                                v)))))
                    (if (equal? next current)
                        current
                        (grow next)))))))
      (let loop ((grid g) (seeds colored))
        (cond
          ((null? seeds) grid)
          (else
           (let* ((seed (car seeds))
                  (sr (first seed))
                  (sc (second seed))
                  (clr (third seed))
                  (g2 (set-cell grid sr sc 0))
                  (g3 (flood-8 g2 sr sc clr)))
             (loop g3 (cdr seeds))))))))))
