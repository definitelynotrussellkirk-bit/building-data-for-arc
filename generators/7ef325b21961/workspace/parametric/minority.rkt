(rule! (lambda (g)
         (let* ((h (rows g))
                (w (cols g)))
           (let* ((all-objs (objects g 0))
                  (big-frames (filter (lambda (o) (>= (length (obj-cells o)) 5))
                                      all-objs))
                  (base (cellmap g (r c v) 0))
                  (with-frames (paint-objects-by base
                                                 big-frames
                                                 (lambda (obj) (obj-color obj)))))
             (reduce (lambda (gr frame)
                       (with-bbox frame
                                  (r1 c1 r2 c2)
                                  (let* ((sh (+ 1 (- r2 r1)))
                                         (sw (+ 1 (- c2 c1)))
                                         (frame-cells (obj-cells frame))
                                         (in-frame? (lambda (r c)
                                                      (ormap (lambda (cell)
                                                               (and
                                                                 (= r (first cell))
                                                                 (= c (second cell))))
                                                             frame-cells)))
                                         (mini (build-grid sh
                                                           sw
                                                           (rr cc)
                                                           (if (in-frame? (+ rr r1)
                                                                          (+ cc c1))
                                                               1
                                                               0)))
                                         (bg-comps (objects mini 1))
                                         (interior-comps (filter (lambda (comp)
                                                                   (not (ormap (lambda (cell)
                                                                                 (let ((r (first cell))
                                                                                       (c (second cell)))
                                                                                   (or
                                                                                     (zero? r)
                                                                                     (= r
                                                                                        (- sh
                                                                                           1))
                                                                                     (zero? c)
                                                                                     (= c
                                                                                        (- sw
                                                                                           1)))))
                                                                               (obj-cells comp))))
                                                                 bg-comps))
                                         (interior-cells (flatmap (lambda (comp)
                                                                    (map (lambda (cell)
                                                                           (list (+ (first cell)
                                                                                    r1)
                                                                                 (+ (second cell)
                                                                                    c1)))
                                                                         (obj-cells comp)))
                                                                  interior-comps))
                                         (interior-colors (filter (lambda (v) (!= v 0))
                                                                  (map (lambda (cell)
                                                                         (at g
                                                                             (first cell)
                                                                             (second cell)))
                                                                       interior-cells)))
                                         (unique-colors (unique interior-colors))
                                         (counts (map (lambda (col)
                                                        (list col
                                                              (count-if (lambda (v)
                                                                          (= v col))
                                                                        interior-colors)))
                                                      unique-colors))
                                         (sorted-counts (sort-by counts
                                                                 (lambda (p)
                                                                   (second p)))))
                                    (if (null? sorted-counts)
                                        gr
                                        (let ((minority (first (first sorted-counts))))
                                          (recolor-cells gr interior-cells minority))))))
                     with-frames
                     big-frames)))))