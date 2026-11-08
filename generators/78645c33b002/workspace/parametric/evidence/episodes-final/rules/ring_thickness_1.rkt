(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((layers (let loop
                               ((r1 0) (c1 0) (r2 (- h 1)) (c2 (- w 1)) (acc (list)))
                               (let* ((outer (at g r1 c1))
                                      (inner-cells (for*/list ((r (range r1 (+ r2 1))) (c (range c1 (+ c2 1)))
                                                       #:when
                                                       (!= (at g r c) outer))
                                                     (list r c))))
                                 (cond
                                   ((null? inner-cells) (reverse (cons outer acc)))
                                   (else (let* ((ir1 (min-of first inner-cells))
                                                (ir2 (max-of first inner-cells))
                                                (ic1 (min-of second inner-cells))
                                                (ic2 (max-of second inner-cells)))
                                           (loop ir1 ic1 ir2 ic2 (cons outer acc))))))))
                  (layers-rev (reverse layers))
                  (n (length layers-rev))
                  (out-size (- (* 2 n) 1)))
             (build-grid out-size
                         out-size
                         (r c)
                         (let* ((mid (quotient out-size 2))
                                (dr (if (< r mid) (- mid r) (- r mid)))
                                (dc (if (< c mid) (- mid c) (- c mid)))
                                (dist (if (> dr dc) dr dc)))
                           (list-ref layers-rev dist)))))))