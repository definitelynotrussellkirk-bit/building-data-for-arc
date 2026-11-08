(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((hh (rows g))
                  (ww (cols g))
                  (gray-row (let loop
                                 ((r 0))
                                 (if (for/and ((c (range 0 ww))) (= (at g r c) 5))
                                     r
                                     (loop (+ r 1)))))
                  (result (make-hash)))
             (for* ((r (range 0 hh)) (c (range 0 ww)))
                   (hash-set! result (list r c) (at g r c)))
             (for* ((r (range 0 hh)) (c (range 0 ww)))
                   (let ((v (at g r c)))
                     (when
                       (or (= v 1) (= v 2))
                       (let* ((above (< r gray-row))
                              (dir (cond
                                     ((and (= v 1) above) -1)
                                     ((and (= v 1) (not above)) 1)
                                     ((and (= v 2) above) 1)
                                     (else -1))))
                         (let loop
                              ((rr (+ r dir)))
                              (when
                                (and (>= rr 0) (< rr hh) (zero? (at g rr c)))
                                (hash-set! result (list rr c) v)
                                (loop (+ rr dir))))))))
             (build-grid hh ww (r c) (hash-ref result (list r c) 0))))))