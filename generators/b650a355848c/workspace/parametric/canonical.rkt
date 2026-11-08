(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((all-objs (objects g 0))
                  (shapes (filter (lambda (o) (= (obj-color o) 6)) all-objs))
                  (markers (let ((s (list)))
                             (for* ((r (range 0 h)) (c (range 0 w)))
                                   (let ((v (at g r c)))
                                     (when
                                       (and (!= v 0) (!= v 6))
                                       (set! s (cons (list r c v) s)))))
                             s))
                  (dist-to-bbox (lambda (mr mc r1 r2 c1 c2)
                                  (let ((dr (if (and (<= r1 mr) (<= mr r2))
                                                0
                                                (min (abs (- mr r1)) (abs (- mr r2)))))
                                        (dc (if (and (<= c1 mc) (<= mc c2))
                                                0
                                                (min (abs (- mc c1)) (abs (- mc c2))))))
                                    (+ dr dc))))
                  (shape-info (map (lambda (shape)
                                     (let* ((cells (obj-cells shape)))
                                       (with-bbox shape
                                                  (r1 c1 r2 c2)
                                                  (let* ((best-marker (let loop
                                                                           ((ms markers) (best #f)
                                                                             (best-dist 99999))
                                                                           (cond
                                                                             ((null? ms) best)
                                                                             (else (let* ((m (car ms))
                                                                                          (d (dist-to-bbox (first m)
                                                                                                           (second m)
                                                                                                           r1
                                                                                                           r2
                                                                                                           c1
                                                                                                           c2)))
                                                                                     (if (< d
                                                                                            best-dist)
                                                                                         (loop (cdr ms)
                                                                                               m
                                                                                               d)
                                                                                         (loop (cdr ms)
                                                                                               best
                                                                                               best-dist))))))))
                                                    (list cells
                                                          r1
                                                          r2
                                                          c1
                                                          c2
                                                          (third best-marker))))))
                                   shapes))
                  (is-vertical (> h w))
                  (sorted-shapes (sort shape-info
                                       (lambda (a b)
                                         (if is-vertical
                                             (< (second a) (second b))
                                             (< (fourth a) (fourth b))))))
                  (n (length sorted-shapes))
                  (out-h (if is-vertical (* n 4) 4))
                  (out-w (if is-vertical 4 (* n 4))))
             (build-grid out-h
                         out-w
                         (gr gc)
                         (let* ((idx (if is-vertical (quotient gr 4) (quotient gc 4)))
                                (base-r (if is-vertical (* idx 4) 0))
                                (base-c (if is-vertical 0 (* idx 4)))
                                (lr (- gr base-r))
                                (lc (- gc base-c))
                                (shape (list-ref sorted-shapes idx))
                                (cells (first shape))
                                (sr1 (second shape))
                                (sc1 (fourth shape))
                                (color (sixth shape)))
                           (let check
                                ((cs cells))
                                (cond
                                  ((null? cs) 0)
                                  ((and
                                     (= (first (car cs)) (+ sr1 lr))
                                     (= (second (car cs)) (+ sc1 lc))) color)
                                  (else (check (cdr cs)))))))))))