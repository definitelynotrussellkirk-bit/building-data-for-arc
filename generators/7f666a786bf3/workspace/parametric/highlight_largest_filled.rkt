(rule! (lambda (g)
  (let* ((base (let ((dummy 0)) (for/fold ((out (empty-grid (rows g) (cols g) 0))) ((color (in-list (grid-colors g 0)))) (let* ((cells (find-color g color)) (bb (bbox-of-cells cells))) (for*/fold ((acc out)) ((r (in-range (first bb) (+ (third bb) 1))) (c (in-range (second bb) (+ (fourth bb) 1)))) (set-cell acc r c color))))))
         (objs (objects base 0)))
    (if (empty? objs)
        base
        (let ((winner (pick-max objs obj-size)))
          (recolor-cells base (obj-cells winner) 9))))))