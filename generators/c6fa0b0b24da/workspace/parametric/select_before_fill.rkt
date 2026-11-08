(rule!
  (let* ((cells (filter-cells g (lambda (r c v) (not (= v 0)))))
         (bb (bbox-of-cells cells))
         (rect-cells
          (positions-in-rect (first bb) (second bb) (third bb) (fourth bb)))
         (zero-mask
          (for/fold ((mask (empty-grid (rows g) (cols g) 0)))
                    ((p (in-list rect-cells)))
            (if (= (at g (first p) (second p)) 0)
                (set-cell mask (first p) (second p) 1)
                mask)))
         (regions (objects zero-mask 0))
         (selected (pick-max regions obj-size))
         ;; Counterfactual wrong order: recolor the selected empty region first.
         (prepaint (recolor-cells g (obj-cells selected) 8))
         ;; Then the bbox fill erases the distinction that Stage B should preserve.
         (pre-cells (filter-cells prepaint (lambda (r c v) (not (= v 0)))))
         (pre-color
          (at prepaint (first (first pre-cells)) (second (first pre-cells))))
         (pre-bb (bbox-of-cells pre-cells)))
    (paint-cells
     (empty-grid (rows g) (cols g) 0)
     (positions-in-rect
      (first pre-bb) (second pre-bb) (third pre-bb) (fourth pre-bb))
     pre-color)))
