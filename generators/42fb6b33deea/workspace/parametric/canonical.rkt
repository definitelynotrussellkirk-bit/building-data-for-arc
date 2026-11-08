(rule!
  (for/fold ([out (empty-grid (rows g) (cols g) 0)]) ([color (in-list (grid-colors g 0))])
    (let ((cells (find-color g color)))
      (if (= (length cells) 4)
          (let ((bb (bbox-of-cells cells)))
            (paint-cells out (positions-in-rect (first bb) (second bb) (third bb) (fourth bb)) color))
          out))))