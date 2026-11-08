(rule!
  (let* ((frame (first (objects (keep-only g 1) 0)))
         (bb (obj-bbox frame))
         (seeds (filter (lambda (cell)
                          (let ((v (third cell)))
                            (and (not (= v 0))
                                 (not (= v 1))
                                 (> (first cell) (first bb))
                                 (< (first cell) (third bb))
                                 (> (second cell) (second bb))
                                 (< (second cell) (fourth bb)))))
                        (grid-cells g))))
    (define (dist cell r c)
      (let ((dr (abs (- (first cell) r)))
            (dc (abs (- (second cell) c))))
        (+ (* dr dr) (* dc dc))))
    (define (nearest-color r c)
      (let* ((ds (map (lambda (cell) (dist cell r c)) seeds))
             (m (apply min ds))
             (colors (remove-duplicates
                       (map third
                            (filter (lambda (cell) (= (dist cell r c) m)) seeds)))))
        (if (= (length colors) 1) (first colors) 0)))
    (for*/fold ([out g])
               ([r (in-range (+ (first bb) 1) (third bb))]
                [c (in-range (+ (second bb) 1) (fourth bb))])
      (if (= (at g r c) 1)
          out
          (set-cell out r c (nearest-color r c))))))