(rule!
  (let* ((h (rows g))
         (w (cols g))
         (zero-objs
           (filter (lambda (obj) (= (obj-color obj) 0))
                   (objects g -1)))
         (marked
           (for/fold ([out g]) ([obj zero-objs])
             (if (for/or ([p (obj-cells obj)])
                   (or (= (first p) 0)
                       (= (first p) (- h 1))
                       (= (second p) 0)
                       (= (second p) (- w 1))))
                 (recolor-cells out (obj-cells obj) 8)
                 out)))
         (cells (filter-cells marked (lambda (r c v) (not (= v 0)))))
         (bb (bbox-of-cells cells)))
    (if bb
        (subgrid marked (first bb) (second bb) (third bb) (fourth bb))
        (empty-grid 1 1 0))))
