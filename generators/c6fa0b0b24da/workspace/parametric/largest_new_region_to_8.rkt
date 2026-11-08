(rule!
  (let* ((cells (filter-cells g (lambda (r c v) (not (= v 0)))))
         (color (at g (first (first cells)) (second (first cells))))
         (bb (bbox-of-cells cells))
         (rect-cells
          (positions-in-rect (first bb) (second bb) (third bb) (fourth bb)))
         ;; Stage A: construct the canonical solid bbox intermediate.
         (intermediate
          (paint-cells (empty-grid (rows g) (cols g) 0) rect-cells color))
         ;; Only cells created by Stage A are eligible for Stage B.
         (new-mask
          (for/fold ((mask (empty-grid (rows g) (cols g) 0)))
                    ((p (in-list rect-cells)))
            (if (= (at g (first p) (second p)) 0)
                (set-cell mask (first p) (second p) 1)
                mask)))
         (regions (objects new-mask 0))
         (selected (pick-max regions obj-size)))
    (recolor-cells intermediate (obj-cells selected) 8)))
