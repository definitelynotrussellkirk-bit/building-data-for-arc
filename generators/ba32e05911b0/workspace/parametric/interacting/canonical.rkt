(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((result (make-hash))
                  (dummy (for* ((r (range 0 h)) (c (range 0 w)))
                               (hash-set! result (list r c) (at g r c))))
                  (magentas (for*/list ((r (range 0 h)) (c (range 0 w)) #:when (= (at g r c) 6))
                              (list r c))))
             (for ((mag magentas))
               (let trace
                    ((r (- (first mag) 1)) (col (second mag)))
                    (cond
                      ((< r 0) (hash-set! result (list 0 col) 6))
                      ((= (at g r col) 7) (let find-re
                             ((re col))
                             (if (and (< (+ re 1) w) (= (at g r (+ re 1)) 7))
                                 (find-re (+ re 1))
                                 (let ((gc (+ re 1)))
                                   (if (>= gc w)
                                       (hash-set! result (list (+ r 1) col) 6)
                                       (let check
                                            ((cc (+ col 1)) (ok #t))
                                            (cond
                                              ((> cc gc) (if ok
                                                    (begin
                                                      (hash-set! result (list r col) 8)
                                                      (hash-set! result
                                                                 (list (+ r 1) col)
                                                                 4)
                                                      (for ((c (range (+ col 1) (+ re 1))))
                                                        (hash-set! result
                                                                   (list (+ r 1) c)
                                                                   2))
                                                      (hash-set! result
                                                                 (list (+ r 1) gc)
                                                                 3)
                                                      (trace r gc))
                                                    (hash-set! result
                                                               (list (+ r 1) col)
                                                               6)))
                                              ((and
                                                 (< (+ r 1) h)
                                                 (< cc w)
                                                 (= (at g (+ r 1) cc) 7)) (check (+ cc 1) #f))
                                              (else (check (+ cc 1) ok)))))))))
                      (else (hash-set! result (list r col) 2) (trace (- r 1) col)))))
             (cellmap g (r c v) (hash-ref result (list r c) 0))))))