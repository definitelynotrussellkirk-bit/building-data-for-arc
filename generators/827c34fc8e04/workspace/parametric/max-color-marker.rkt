(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((colored (filter (lambda (p) (!= (at g (first p) (second p)) 0))
                                   (grid-positions g)))
                  (ranked (sort colored
                                (lambda (a b)
                                  (let ((va (at g (first a) (second a)))
                                        (vb (at g (first b) (second b))))
                                    (cond [(> va vb) #t]
                                          [(< va vb) #f]
                                          [(= (first a) (first b))
                                           (< (second a) (second b))]
                                          [else (< (first a) (first b))])))))
                  (selected (list (first ranked))))
             (build-grid (* 2 h)
                         (* 2 w)
                         (r c)
                         (let* ((sr (quotient r 2))
                                (sc (quotient c 2))
                                (v (at g sr sc)))
                           (cond
                             ((!= v 0) v)
                             ((any? (lambda (p)
                                      (= (- r c) (* 2 (- (first p) (second p)))))
                                    selected) 1)
                             (else 0))))))))
