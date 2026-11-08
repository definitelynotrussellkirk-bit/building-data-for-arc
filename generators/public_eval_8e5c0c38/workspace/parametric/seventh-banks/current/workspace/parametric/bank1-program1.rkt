(rule!
 ;; Recover per-color vertical symmetry from maximum reflected support.
 ;; The most frequent color is background; ties use the smaller color.
 ;; Each color's axis is a doubled column, so half-cell axes are representable.
 ;; Equal maximum-support axes use the leftmost axis (smallest doubled column).
 ;; Complete missing partners, preserving the input support; clip at the canvas.
 (lambda (g)
  (let ()
   (define bg (pick-max (range 0 10) (lambda (color) (count-color g color))))
   (define (axis cells)
    (pick-max (range 0 (- (* 2 w) 1))
     (lambda (k)
      (count-if (lambda (p) (member (list (first p) (- k (second p))) cells)) cells))))
   (define records
    (for/list ((color (grid-colors g bg)))
     (let ((cells (find-color g color)))
      (list color cells (axis cells)))))
   (for/fold ((out (empty-grid h w bg))) ((part records))
    (let* ((color (first part)) (cells (second part)) (k (third part))
           (partners (map (lambda (p) (list (first p) (- k (second p)))) cells))
           (chosen (remove-duplicates (append cells partners))))
      (recolor-cells out chosen color))))))
