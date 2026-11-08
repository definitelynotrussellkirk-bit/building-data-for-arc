(rule!
  (let* ((objs (sort (objects g 0) (lambda (a b) (> (obj-size a) (obj-size b)))))
         (shapes (map (lambda (obj) (subgrid g (obj-r1 obj) (obj-c1 obj) (obj-r2 obj) (obj-c2 obj))) objs))
         (out-h (+ (apply + (map rows shapes)) (max 0 (- (length shapes) 1))))
         (out-w (apply max (map cols shapes))))
    (let pack ([remaining shapes] [top 0] [out (empty-grid out-h out-w 0)])
      (if (empty? remaining)
          out
          (let* ((shape (first remaining))
                 (next (for*/fold ([acc out])
                                   ([r (in-range (rows shape))]
                                    [c (in-range (cols shape))])
                         (let ((v (at shape r c)))
                           (if (not (= v 0)) (set-cell acc (+ top r) c v) acc)))))
            (pack (rest remaining) (+ top (rows shape) 1) next))))))