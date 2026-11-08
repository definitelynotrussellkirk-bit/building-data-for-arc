(rule! (lambda (g) (flip-lr ((lambda (g) (let* ((h (rows g)) (w (cols g))) ((lambda (g)
         (let* ((h (rows g))
                (w (cols g))
                (starts (filter (lambda (c) (= 2 (at g (- h 1) c))) (range 0 w)))
                (trace-path (lambda (sc)
                              (let* ((max-iter (* h w))
                                     (result (reduce (lambda (state _)
                                                       (let ((r (first state))
                                                             (c (second state))
                                                             (cells (third state))
                                                             (stopped (fourth state)))
                                                         (if stopped
                                                             state
                                                             (cond
                                                               ((and
                                                                  (> r 0)
                                                                  (!= 5
                                                                      (at g (- r 1) c))) (list (- r 1)
                                                                       c
                                                                       (append cells
                                                                               (list (list (- r
                                                                                              1)
                                                                                           c)))
                                                                       #f))
                                                               ((and
                                                                  (> r 0)
                                                                  (< (+ c 1) w)
                                                                  (!= 5
                                                                      (at g r (+ c 1)))
                                                                  (= 5 (at g (- r 1) c))) (list r
                                                                       (+ c 1)
                                                                       (append cells
                                                                               (list (list r
                                                                                           (+ c
                                                                                              1))))
                                                                       #f))
                                                               (else (list r c cells #t))))))
                                                     (list (- h 1)
                                                           sc
                                                           (list (list (- h 1) sc))
                                                           #f)
                                                     (range 0 max-iter))))
                                (third result))))
                (all-cells (reduce append (list) (map trace-path starts))))
           (cellmap g (r c v) (if (member? (list r c) all-cells) 2 v)))) g))) (flip-lr g)))))
