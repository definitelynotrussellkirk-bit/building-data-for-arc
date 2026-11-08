(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((all-colors (grid-colors g))
                  (div-color (find (lambda (clr)
                                     (or
                                       (for/or ((r (range 0 h)))
                                               (for/and ((cc (range 0 w)))
                                                        (= (at g r cc) clr)))
                                       (for/or ((cc (range 0 w)))
                                               (for/and ((r (range 0 h)))
                                                        (= (at g r cc) clr)))))
                                   all-colors))
                  (cell-color (find (lambda (clr) (!= clr div-color)) all-colors))
                  (div-rows (for/list ((r (range 0 h)) #:when
                                (for/and ((cc (range 0 w))) (= (at g r cc) div-color)))
                              r))
                  (div-cols (for/list ((cc (range 0 w)) #:when
                                (for/and ((r (range 0 h))) (= (at g r cc) div-color)))
                              cc))
                  (row-band-sizes
                    (let loop
                         ((divs (append (list -1) div-rows (list h))) (sizes (list)))
                         (cond
                           ((null? (cdr divs)) sizes)
                           ((> (- (cadr divs) (car divs)) 1)
                            (loop (cdr divs)
                                  (append sizes
                                          (list (- (cadr divs) (car divs) 1)))))
                           (else (loop (cdr divs) sizes)))))
                  (col-band-sizes
                    (let loop
                         ((divs (append (list -1) div-cols (list w))) (sizes (list)))
                         (cond
                           ((null? (cdr divs)) sizes)
                           ((> (- (cadr divs) (car divs)) 1)
                            (loop (cdr divs)
                                  (append sizes
                                          (list (- (cadr divs) (car divs) 1)))))
                           (else (loop (cdr divs) sizes))))))
             (build-grid (length row-band-sizes)
                         (length col-band-sizes)
                         (r c)
                         (if (odd? (* (list-ref row-band-sizes r)
                                      (list-ref col-band-sizes c)))
                             cell-color
                             div-color))))))
