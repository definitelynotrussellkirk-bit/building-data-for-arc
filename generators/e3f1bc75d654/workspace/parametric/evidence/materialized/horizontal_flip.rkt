(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (visited (make-hash))
                  (frames (list))
                  (dummy-f (for* ((r (range 0 hh)) (c (range 0 ww)))
                                 (when
                                   (and
                                     (!= (at g r c) 0)
                                     (not (hash-has-key? visited (list r c))))
                                   (let ((color (at g r c))
                                         (comp (list))
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
                                                    (>= cr hh)
                                                    (< cc 0)
                                                    (>= cc ww)
                                                    (!= (at g cr cc) color)
                                                    (hash-has-key? visited (list cr cc)))
                                                  (bfs rest)
                                                  (begin
                                                    (hash-set! visited (list cr cc) #t)
                                                    (set! comp (cons (list cr cc) comp))
                                                    (bfs (append (list (list (- cr 1)
                                                                             cc)
                                                                       (list (+ cr 1)
                                                                             cc)
                                                                       (list cr
                                                                             (- cc 1))
                                                                       (list cr
                                                                             (+ cc 1)))
                                                                 rest)))))))
                                     (let* ((rs (map first comp))
                                            (cs2 (map second comp))
                                            (rmin (min-list rs))
                                            (rmax (max-list rs))
                                            (cmin (min-list cs2))
                                            (cmax (max-list cs2))
                                            (ih (- rmax rmin 1))
                                            (iw (- cmax cmin 1))
                                            (has-pat (for/or ((dr (range 1
                                                                         (- rmax rmin))))
                                                             (for/or ((dc (range 1
                                                                                 (- cmax
                                                                                    cmin))))
                                                                     (= (at g
                                                                            (+ rmin dr)
                                                                            (+ cmin dc))
                                                                        color)))))
                                       (set! frames
                                             (cons (list color
                                                         rmin
                                                         cmin
                                                         rmax
                                                         cmax
                                                         ih
                                                         iw
                                                         has-pat)
                                                   frames)))))))
                  (template (car (filter (lambda (f) (list-ref f 7)) frames)))
                  (t-color (first template))
                  (t-rmin (second template))
                  (t-cmin (third template))
                  (t-ih (list-ref template 5))
                  (t-iw (list-ref template 6))
                  (result (make-hash))
                  (dummy-draw (for ((frame frames))
                                (let ((fc (first frame))
                                      (rmin (second frame))
                                      (cmin (third frame))
                                      (rmax (list-ref frame 3))
                                      (cmax (list-ref frame 4))
                                      (ih (list-ref frame 5))
                                      (iw (list-ref frame 6)))
                                  (when
                                    (and (= ih t-ih) (= iw t-iw))
                                    (for* ((r (range rmin (+ rmax 1))) (c (range cmin (+ cmax 1))))
                                          (when
                                            (or
                                              (= r rmin)
                                              (= r rmax)
                                              (= c cmin)
                                              (= c cmax))
                                            (hash-set! result (list r c) fc)))
                                    (for* ((dr (range 0 ih)) (dc (range 0 iw)))
                                          (when
                                            (= (at g (+ t-rmin 1 dr) (+ t-cmin 1 dc))
                                               t-color)
                                            (hash-set! result
                                                       (list (+ rmin 1 dr)
                                                             (+ cmin 1 (- iw 1 dc)))
                                                       fc))))))))
             (build-grid hh ww (r c) (hash-ref result (list r c) 0))))))
