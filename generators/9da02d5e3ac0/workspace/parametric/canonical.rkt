(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (cellmap g
                    (r c v)
                    (let ((nz (filter (lambda (v) (!= v 5))
                                      (map (lambda (cc) (at g r cc)) (range 0 w)))))
                      (if (and (= 5 v) (not (null? nz))) (first nz) v))))))