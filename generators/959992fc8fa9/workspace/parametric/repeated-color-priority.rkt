(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (pixels (for*/list ((r (range 0 h)) (c (range 0 w)) #:when (!= (at g r c) 0))
                          (list r c (at g r c))))
                (priority (let find-priority
                     ((rest pixels))
                     (if (null? rest)
                         -1
                         (let* ((p (car rest))
                                (candidate (third p))
                                (count (for/sum ((q pixels))
                                         (if (= (third q) candidate) 1 0))))
                           (if (> count 1)
                               candidate
                               (find-priority (cdr rest))))))))
           (cellmap g
                    (r c v)
                    (let loop
                         ((ps pixels) (colors (list)))
                         (cond
                           ((null? ps) (cond
                               ((null? colors) 0)
                               ((null? (cdr colors)) (first colors))
                               ((member priority colors) priority)
                               (else 2)))
                           (else (let* ((p (car ps))
                                        (pr (first p))
                                        (pc (second p))
                                        (pcol (third p)))
                                   (if (or (= r pr) (= c pc))
                                       (if (member pcol colors)
                                           (loop (cdr ps) colors)
                                           (loop (cdr ps) (cons pcol colors)))
                                       (loop (cdr ps) colors))))))))))