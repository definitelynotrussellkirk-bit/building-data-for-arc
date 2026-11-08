(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((pixels (for*/list ((r (range 0 h)) (c (range 0 w)) #:when (!= (at g r c) 0))
                            (list r c (at g r c)))))
             (cellmap g
                      (r c v)
                      (let loop
                           ((ps pixels) (colors (list)))
                           (cond
                             ((null? ps) (cond
                                 ((null? colors) 0)
                                 ((null? (cdr colors)) (first colors))
                                 (else 2)))
                             (else (let* ((p (car ps))
                                          (pr (first p))
                                          (pc (second p))
                                          (pcol (third p)))
                                     (if (or (= r pr) (= c pc))
                                         (if (member pcol colors)
                                             (loop (cdr ps) colors)
                                             (loop (cdr ps) (cons pcol colors)))
                                         (loop (cdr ps) colors)))))))))))