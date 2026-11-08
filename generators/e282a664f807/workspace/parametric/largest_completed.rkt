(rule!
 (let ((dummy 0))
  (define (paint grid cells color)
   (for/fold ((out grid)) ((p (in-list cells)))
    (if (in-bounds? (first p) (second p) (rows out) (cols out))
        (set-cell out (first p) (second p) color)
        out)))
  (let* ((pair-colors
          (filter (lambda (v) (= (length (find-color g v)) 2))
                  (grid-colors g 0)))
         (intermediate
          (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                    ((v (in-list pair-colors)))
           (let ((bb (bbox-of-cells (find-color g v))))
            (paint out
                   (positions-in-rect (first bb) (second bb) (third bb) (fourth bb))
                   v))))
         (selected
          (pick-max pair-colors (lambda (v) (count-color intermediate v)))))
   (paint intermediate (find-color intermediate selected) 9))))
