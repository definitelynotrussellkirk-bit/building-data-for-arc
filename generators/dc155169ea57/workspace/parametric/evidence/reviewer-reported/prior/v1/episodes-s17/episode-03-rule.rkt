(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (red-row #f)
                  (d0 (for ((r (range 0 hh)))
                        (when
                          (and
                            (not red-row)
                            (for/and ((c (range 0 ww))) (= (at g r c) 2)))
                          (set! red-row r))))
                  (vis (make-hash))
                  (shapes (list))
                  (d1 (for* ((r (range 0 red-row)) (c (range 0 ww)))
                            (when
                              (and
                                (= (at g r c) 1)
                                (not (hash-has-key? vis (list r c))))
                              (let ((comp (list))
                                    (stack (list (list r c))))
                                (let bfs
                                     ((stk stack))
                                     (unless
                                       (null? stk)
                                       (let* ((cur (car stk))
                                              (rest (cdr stk))
                                              (cr (first cur))
                                              (cc (second cur)))
                                         (if (or
                                               (< cr 0)
                                               (>= cr red-row)
                                               (< cc 0)
                                               (>= cc ww)
                                               (!= (at g cr cc) 1)
                                               (hash-has-key? vis (list cr cc)))
                                             (bfs rest)
                                             (begin
                                               (hash-set! vis (list cr cc) #t)
                                               (set! comp (cons (list cr cc) comp))
                                               (bfs (append (list (list (- cr 1) cc)
                                                                  (list (+ cr 1) cc)
                                                                  (list cr (- cc 1))
                                                                  (list cr (+ cc 1)))
                                                            rest)))))))
                                (set! shapes (cons comp shapes))))))
                  (result (build-grid hh
                                      ww
                                      (r c)
                                      (if (and (< r red-row) (= (at g r c) 1))
                                          8
                                          (at g r c))))
                  (pass-cols (make-hash))
                  (d2 (for ((shape shapes))
                        (let* ((rmin (min-of first shape))
                               (rmax (max-of first shape))
                               (cmin (min-of second shape))
                               (cmax (max-of second shape)))
                          (define (row-count rr)
                            (for/sum ((p shape)) (if (= (first p) rr) 1 0)))
                          (define wide-rows
                            (filter (lambda (rr) (> (row-count rr) 3))
                                    (range rmin (+ rmax 1))))
                          (define no-wide (null? wide-rows))
                          (define dr
                            (if no-wide
                                (- (- hh 1) rmax)
                                (- (- red-row 1) (max-list wide-rows))))
                          (when
                            no-wide
                            (for ((cell shape)) (hash-set! pass-cols (second cell) #t)))
                          (for ((cell shape))
                            (let ((nr (+ (first cell) dr))
                                  (nc (second cell)))
                              (when
                                (in-bounds? nr nc hh ww)
                                (set! result (set-cell result nr nc 1))))))))
                  (d3 (for ((c (hash-keys pass-cols)))
                        (set! result (set-cell result red-row c 8)))))
             result))))