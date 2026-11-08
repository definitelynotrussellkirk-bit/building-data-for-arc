(rule! (lambda (g)
         (define objs (objects g 0))
         (define comps
           (map (lambda (o)
                  (let* ((cells (obj-cells o))
                         (color (at g (first (first cells)) (second (first cells)))))
                    (list color cells)))
                objs))
         (define (normalize cells)
           (let* ((bb (bbox-of-cells cells))
                  (mr (first bb))
                  (mc (second bb)))
             (sort-by (map (lambda (p) (list (- (first p) mr) (- (second p) mc))) cells)
                      (lambda (p) (+ (* (first p) 100) (second p))))))
         (define (vflip cells)
           (map (lambda (p) (list (- 0 (first p)) (second p))) cells))
         (define (add-unique lst item)
           (if (any? (lambda (x) (= x item)) lst) lst (cons item lst)))
         (define (orientations cells allow-rot allow-refl)
           (define result (list (normalize cells)))
           (if allow-rot
               (reverse (let loop
                             ((cur cells) (i 0) (acc result))
                             (if (>= i 3)
                                 acc
                                 (let ((next (rotate-cells-cw cur)))
                                   (loop next (+ i 1) (add-unique acc (normalize next)))))))
               result))
         (define OUT-H 3)
         (define OUT-W 4)
         (define (try-solve allow-rot allow-refl)
           (define comp-or
             (sort-by (map (lambda (c)
                             (let* ((color (first c))
                                    (cells (second c))
                                    (oris (orientations cells allow-rot allow-refl))
                                    (oris-with-refl (if allow-refl
                                                        (let loop
                                                             ((cur (vflip cells)) (i 0)
                                                               (acc oris))
                                                             (if (>= i 4)
                                                                 acc
                                                                 (loop (rotate-cells-cw cur)
                                                                       (+ i 1)
                                                                       (add-unique acc
                                                                                   (normalize cur)))))
                                                        oris)))
                               (list color oris-with-refl)))
                           comps)
                      (lambda (c) (+ (* -100 (length (first (second c)))) (first c)))))
           (define (try-place grid idx)
             (if (>= idx (length comp-or))
                 (if (andmap (lambda (p) (not (= (at grid (first p) (second p)) 0)))
                             (grid-positions grid))
                     grid
                     #f)
                 (let* ((cur (nth comp-or idx))
                        (color (first cur))
                        (oris (second cur)))
                   (let try-oris
                        ((os oris))
                        (if (null? os)
                            #f
                            (let* ((shape (first os)))
                              (let try-pos
                                   ((dr 0) (dc 0))
                                   (cond
                                     ((>= dr OUT-H) (try-oris (cdr os)))
                                     ((>= dc OUT-W) (try-pos (+ dr 1) 0))
                                     (else (let ((can-place (andmap (lambda (p)
                                                                      (let ((nr (+ dr
                                                                                   (first p)))
                                                                            (nc (+ dc
                                                                                   (second p))))
                                                                        (and
                                                                          (>= nr 0)
                                                                          (< nr OUT-H)
                                                                          (>= nc 0)
                                                                          (< nc OUT-W)
                                                                          (= (at grid
                                                                                 nr
                                                                                 nc)
                                                                             0))))
                                                                    shape)))
                                             (if can-place
                                                 (let* ((new-grid (paint-cells grid
                                                                               (map (lambda (p)
                                                                                      (list (+ dr
                                                                                               (first p))
                                                                                            (+ dc
                                                                                               (second p))))
                                                                                    shape)
                                                                               color))
                                                        (result (try-place new-grid
                                                                           (+ idx 1))))
                                                   (if result
                                                       result
                                                       (try-pos dr (+ dc 1))))
                                                 (try-pos dr (+ dc 1)))))))))))))
           (try-place (grid-from-fn OUT-H OUT-W (lambda (r c) 0)) 0))
         (let ((r1 (try-solve #f #f)))
           (if r1 r1 (let ((r2 (try-solve #t #f))) (if r2 r2 (try-solve #t #t)))))))