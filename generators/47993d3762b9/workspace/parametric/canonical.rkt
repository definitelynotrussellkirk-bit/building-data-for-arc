(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([color (in-list (grid-colors g 0))])
    (let* ((bb (bbox-of-cells (find-color g color)))
           (corners (list (list (first bb) (second bb) color)
                          (list (first bb) (fourth bb) color)
                          (list (third bb) (second bb) color)
                          (list (third bb) (fourth bb) color))))
      (paint-cells out corners))))