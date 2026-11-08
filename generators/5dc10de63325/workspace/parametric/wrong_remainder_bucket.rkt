(rule! (lambda (g)
         (let* ((count (length (find-color g 8)))
                (per-quad (quotient count 4))
                (wrong (+ (remainder count 4) 1))
                (markers
                 (sort
                  (filter (lambda (p)
                            (let ((v (at g (first p) (second p))))
                              (and (not (= v 0)) (not (= v 8)))))
                          (grid-positions g))
                  (lambda (a b)
                    (or (< (first a) (first b))
                        (and (= (first a) (first b))
                             (< (second a) (second b)))))))
                (selected (list-ref markers (- wrong 1)))
                (selected-color (at g (first selected) (second selected)))
                (tile (cond
                        ((= per-quad 4) (list (list 8 8) (list 8 8)))
                        ((= per-quad 3) (list (list 0 8) (list 8 8)))
                        ((= per-quad 2) (list (list 0 0) (list 8 8)))
                        ((= per-quad 1) (list (list 0 0) (list 0 8)))
                        (else (list (list 0 0) (list 0 0)))))
                (base
                 (build-grid 5
                             5
                             (r c)
                             (cond
                               ((= r 2) 0)
                               ((= c 2) 0)
                               (else
                                (let ((tr (remainder (if (> r 2) (- r 3) r) 2))
                                      (tc (remainder (if (> c 2) (- c 3) c) 2)))
                                  (list-ref (list-ref tile tr) tc)))))))
           (set-cell base 2 2 selected-color))))
