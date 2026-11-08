(rule!
  (let* ((cells (filter-cells g (lambda (r c v) (not (= v 0)))))
         (color (at g (first (first cells)) (second (first cells))))
         (bb (bbox-of-cells cells)))
    (paint-cells (empty-grid (rows g) (cols g) 0)
                 (positions-in-rect (first bb) (second bb) (third bb) (fourth bb))
                 color)))