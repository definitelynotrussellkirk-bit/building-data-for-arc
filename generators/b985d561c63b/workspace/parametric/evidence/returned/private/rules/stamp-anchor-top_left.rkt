(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (template-cells (for*/list ((r (range 0 hh)) (c (range 0 ww))
                                      #:when
                                      (and (!= (at g r c) 0) (!= (at g r c) 5)))
                                    (list r c (at g r c))))
                  (tr1 (min-of first template-cells))
                  (tc1 (min-of second template-cells))
                  (tr2 (max-of first template-cells))
                  (tc2 (max-of second template-cells))
                  (th (+ 1 (- tr2 tr1)))
                  (tw (+ 1 (- tc2 tc1)))
                  (visited (make-hash))
                  (gray-regions (list))
                  (dummy (for* ((r (range 0 hh)) (c (range 0 ww)))
                               (when
                                 (and
                                   (= (at g r c) 5)
                                   (not (hash-has-key? visited (list r c))))
                                 (let ((cells (list)))
                                   (let bfs
                                        ((q (list (list r c))))
                                        (unless
                                          (null? q)
                                          (let ((cr (first (car q)))
                                                (cc (second (car q))))
                                            (cond
                                              ((or
                                                 (hash-has-key? visited (list cr cc))
                                                 (< cr 0)
                                                 (>= cr hh)
                                                 (< cc 0)
                                                 (>= cc ww)
                                                 (!= (at g cr cc) 5)) (bfs (cdr q)))
                                              (else (hash-set! visited (list cr cc) #t)
                                                    (set! cells
                                                          (cons (list cr cc) cells))
                                                    (bfs (append (cdr q)
                                                                 (list (list (- cr 1)
                                                                             cc)
                                                                       (list (+ cr 1)
                                                                             cc)
                                                                       (list cr
                                                                             (- cc 1))
                                                                       (list cr
                                                                             (+ cc 1))))))))))
                                   (set! gray-regions
                                         (append gray-regions (list cells)))))))
                  (result (make-hash)))
             (for* ((r (range 0 hh)) (c (range 0 ww)))
                   (hash-set! result (list r c) (at g r c)))
             (for ((region gray-regions))
               (let ((rmin (min-of first region))
                     (cmin (min-of second region)))
                 (for* ((dr (range 0 th)) (dc (range 0 tw)))
                       (let ((nr (+ rmin dr))
                             (nc (+ cmin dc)))
                         (when
                           (and (>= nr 0) (< nr hh) (>= nc 0) (< nc ww))
                           (hash-set! result (list nr nc) (at g (+ tr1 dr) (+ tc1 dc))))))))
             (build-grid hh ww (r c) (hash-ref result (list r c) 0))))))