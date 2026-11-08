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
         ;; Wrong order: choose from the raw two-cell candidates while all
         ;; candidates are tied, before completion reveals their areas.
         (selected (pick-min pair-colors (lambda (v) v)))
         (intermediate
          (for/fold ((out (empty-grid (rows g) (cols g) 0)))
                    ((v (in-list pair-colors)))
           (let ((bb (bbox-of-cells (find-color g v))))
            (paint out
                   (positions-in-rect (first bb) (second bb) (third bb) (fourth bb))
                   v)))))
   (paint intermediate (find-color intermediate selected) 9))))
