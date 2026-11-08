(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((bg (mode g))
                  (all-objs (objects g bg))
                  (non-border (filter (lambda (o)
                                        (with-bbox o
                                                   (r1 c1 r2 c2)
                                                   (not (and
                                                          (zero? r1)
                                                          (zero? c1)
                                                          (= r2 (- h 1))
                                                          (= c2 (- w 1))))))
                                      all-objs))
                  (sorted-shapes (sort non-border
                                       (lambda (a b) (> (obj-size a) (obj-size b)))))
                  (placements (let loop
                                   ((shapes sorted-shapes) (col-off 0) (acc (list)))
                                   (cond
                                     ((null? shapes) (reverse acc))
                                     (else (let* ((s (car shapes)))
                                             (with-bbox s
                                                        (r1 c1 r2 c2)
                                                        (let* ((sh (+ 1 (- r2 r1)))
                                                               (sw (+ 1 (- c2 c1)))
                                                               (new-r1 (- h sh))
                                                               (new-c1 col-off))
                                                          (loop (cdr shapes)
                                                                (+ col-off sw)
                                                                (cons (list s
                                                                            r1
                                                                            c1
                                                                            new-r1
                                                                            new-c1)
                                                                      acc))))))))))
             (for/fold ((out (cellmap g (r c v) bg)))
               ((pl placements))
               (let* ((shape (first pl))
                      (orig-r1 (second pl))
                      (orig-c1 (third pl))
                      (new-r1 (fourth pl))
                      (new-c1 (fifth pl))
                      (cells (obj-cells shape)))
                 (for/fold ((gg out))
                   ((cell cells))
                   (let* ((r (first cell))
                          (c (second cell))
                          (nr (+ (- r orig-r1) new-r1))
                          (nc (+ (- c orig-c1) new-c1)))
                     (set-cell gg nr nc (at g r c))))))))))
