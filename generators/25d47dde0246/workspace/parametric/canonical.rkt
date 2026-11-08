(rule!
  (let* ((cells (filter-cells g (lambda (r c v) (not (= v 0)))))
         (bb (bbox-of-cells cells)))
    (if bb
        (subgrid g (first bb) (second bb) (third bb) (fourth bb))
        (empty-grid 1 1 0))))