(rule!
  (let* ((cells (filter-cells g (lambda (r c v) (not (= v 0)))))
         (bb (bbox-of-cells cells)))
    (if bb
        (let* ((stage (subgrid g (first bb) (second bb) (third bb) (fourth bb)))
               (h (rows stage))
               (w (cols stage))
               (zero-objs
                 (filter (lambda (obj) (= (obj-color obj) 0))
                         (objects stage -1))))
          (for/fold ([out stage]) ([obj zero-objs])
            (if (for/or ([p (obj-cells obj)])
                  (or (= (first p) 0)
                      (= (first p) (- h 1))
                      (= (second p) 0)
                      (= (second p) (- w 1))))
                (recolor-cells out (obj-cells obj) 8)
                out)))
        (empty-grid 1 1 0))))
