(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((global-bg (mode g))
                  (full-row (let ((rows-found (for/list ((r (range 0 h)) #:when
                                                  (let ((v (at g r 0)))
                                                    (and
                                                      (!= v global-bg)
                                                      (for/and ((c (range 0 w)))
                                                               (= (at g r c) v)))))
                                                r)))
                              (if (null? rows-found) #f (first rows-found))))
                  (full-col (let ((cols-found (for/list ((c (range 0 w)) #:when
                                                  (let ((v (at g 0 c)))
                                                    (and
                                                      (!= v global-bg)
                                                      (for/and ((r (range 0 h)))
                                                               (= (at g r c) v)))))
                                                c)))
                              (if (null? cols-found) #f (first cols-found)))))
             (cond
               (full-row
                 (let* ((sep-r full-row)
                        (src-bg (mode-list (for*/list ((r (range 0 sep-r)) (c (range 0 w)))
                                             (at g r c))))
                        (key-r (+ sep-r 1))
                        (near-r (- sep-r 1))
                        (far-r 0)
                        (relay-r 1)
                        (stage-a
                          (for*/fold ((out g))
                                     ((r (range 0 sep-r)) (c (range 0 w)))
                            (let ((v (at g r c)))
                              (if (= v src-bg)
                                  out
                                  (let* ((key (at g key-r c))
                                         (dest-r (if (= v key) near-r far-r))
                                         (cleared (set-cell out r c src-bg)))
                                    (set-cell cleared dest-r c v))))))
                        (near-cols (for/list ((c (range 0 w)) #:when
                                               (!= (at stage-a near-r c) src-bg))
                                     c))
                        (far-cols (for/list ((c (range 0 w)) #:when
                                              (!= (at stage-a far-r c) src-bg))
                                    c))
                        (k (length near-cols))
                        (selected-c (list-ref far-cols 0))
                        (selected-v (at stage-a far-r selected-c))
                        (cleared (set-cell stage-a far-r selected-c src-bg)))
                   (set-cell cleared relay-r selected-c selected-v)))
               (else
                 (let* ((sep-c full-col)
                        (src-bg (mode-list (for*/list ((r (range 0 h)) (c (range (+ sep-c 1) w)))
                                             (at g r c))))
                        (key-c (- sep-c 1))
                        (near-c (+ sep-c 1))
                        (far-c (- w 1))
                        (relay-c (- w 2))
                        (stage-a
                          (for*/fold ((out g))
                                     ((r (range 0 h)) (c (range (+ sep-c 1) w)))
                            (let ((v (at g r c)))
                              (if (= v src-bg)
                                  out
                                  (let* ((key (at g r key-c))
                                         (dest-c (if (= v key) near-c far-c))
                                         (cleared (set-cell out r c src-bg)))
                                    (set-cell cleared r dest-c v))))))
                        (near-rows (for/list ((r (range 0 h)) #:when
                                               (!= (at stage-a r near-c) src-bg))
                                     r))
                        (far-rows (for/list ((r (range 0 h)) #:when
                                              (!= (at stage-a r far-c) src-bg))
                                    r))
                        (k (length near-rows))
                        (selected-r (list-ref far-rows 0))
                        (selected-v (at stage-a selected-r far-c))
                        (cleared (set-cell stage-a selected-r far-c src-bg)))
                   (set-cell cleared selected-r relay-c selected-v))))))))
