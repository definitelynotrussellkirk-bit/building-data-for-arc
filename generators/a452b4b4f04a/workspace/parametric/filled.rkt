(rule!
  (let ((colors (filter (lambda (v) (not (= v 0))) (grid-colors g))))
    (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([color (in-list colors)])
      (let* ((pts (find-color g color))
             (bb (bbox-of-cells pts)))
        (paint-cells out
                     (positions-in-rect (first bb) (second bb) (third bb) (fourth bb))
                     color)))))
