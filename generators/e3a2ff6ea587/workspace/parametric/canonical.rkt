(rule!
 ;; A color whose four cells sit EXACTLY at its bbox corners gets the whole
 ;; bbox FILLED with that color; every other color's cells are dropped.
 ;; (Colors iterate in first-appearance order — overlap paint order matters.)
 (let ((colors (remove-duplicates
                (map third (filter (lambda (cell) (!= (third cell) 0))
                                   (grid-cells g))))))
   (for/fold ((out (empty-grid h w 0))) ((color (in-list colors)))
     (let* ((cells (find-color g color))
            (bb (bbox-of-cells cells))
            (corners (list (list (first bb) (second bb))
                           (list (first bb) (fourth bb))
                           (list (third bb) (second bb))
                           (list (third bb) (fourth bb)))))
       (if (and (= (length cells) 4)
                (all? (lambda (p) (member? p corners)) cells))
           (paint-cells out
                        (positions-in-rect (first bb) (second bb)
                                           (third bb) (fourth bb))
                        color)
           out)))))