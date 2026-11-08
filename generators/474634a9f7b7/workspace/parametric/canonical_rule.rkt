(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg 8)
                  (shapes (objects-8 g bg))
                  (shape-infos (map (lambda (o)
                                      (let* ((cells (obj-cells o))
                                             (color (obj-color o))
                                             (bb (obj-bbox o))
                                             (size (length cells))
                                             (cr (/ (- h 1) 2.0))
                                             (cc (/ (- w 1) 2.0))
                                             (tip (let loop
                                                       ((cs cells) (best #f)
                                                         (best-d 1e18))
                                                       (cond
                                                         ((null? cs) best)
                                                         (else (let* ((c (car cs))
                                                                      (cr2 (first c))
                                                                      (cc2 (second c))
                                                                      (d (+ (* (- cr2
                                                                                  cr)
                                                                               (- cr2
                                                                                  cr))
                                                                            (* (- cc2
                                                                                  cc)
                                                                               (- cc2
                                                                                  cc)))))
                                                                 (if (< d best-d)
                                                                     (loop (cdr cs) c d)
                                                                     (loop (cdr cs)
                                                                           best
                                                                           best-d))))))))
                                        (list color
                                              cells
                                              (first bb)
                                              (second bb)
                                              (third bb)
                                              (fourth bb)
                                              size
                                              tip)))
                                    shapes))
                  (target (let loop
                               ((ss shape-infos) (best #f) (best-size -1))
                               (cond
                                 ((null? ss) best)
                                 (else (let* ((si (car ss))
                                              (sz (seventh si)))
                                         (if (> sz best-size)
                                             (loop (cdr ss) si sz)
                                             (loop (cdr ss) best best-size)))))))
                  (target-color (first target))
                  (target-r1 (third target))
                  (target-c1 (fourth target))
                  (target-r2 (fifth target))
                  (target-c2 (sixth target))
                  (target-tip (eighth target))
                  (tip-r (first target-tip))
                  (tip-c (second target-tip))
                  (body-cr (/ (+ target-r1 target-r2) 2.0))
                  (body-cc (/ (+ target-c1 target-c2) 2.0))
                  (dr-t (- tip-r body-cr))
                  (dc-t (- tip-c body-cc))
                  (paint-bar (lambda (base cells)
                               (paint-cells base
                                            (filter (lambda (p)
                                                      (in-bounds? (first p)
                                                                  (second p)
                                                                  h
                                                                  w))
                                                    cells)
                                            target-color)))
                  (g1 (erase-cells g
                                   (map eighth
                                        (filter (lambda (si) (not (equal? si target)))
                                                shape-infos))
                                   bg))
                  (g2 (cond
                        ((> (abs dr-t) (abs dc-t)) (if (> dr-t 0)
                              (let ((new-row (- target-r1 1)))
                                (paint-bar g1
                                           (map (lambda (dc)
                                                  (list new-row (+ tip-c dc)))
                                                (list -1 0 1))))
                              (let ((new-row (+ target-r2 1)))
                                (paint-bar g1
                                           (map (lambda (dc)
                                                  (list new-row (+ tip-c dc)))
                                                (list -1 0 1))))))
                        (else (if (> dc-t 0)
                                  (let ((new-col (- target-c1 1)))
                                    (paint-bar g1
                                               (map (lambda (dr)
                                                      (list (+ tip-r dr) new-col))
                                                    (list -1 0 1))))
                                  (let ((new-col (+ target-c2 1)))
                                    (paint-bar g1
                                               (map (lambda (dr)
                                                      (list (+ tip-r dr) new-col))
                                                    (list -1 0 1)))))))))
             g2))))