(rule!
  (let ()
    (define (bbox-area cells)
      (let ((bb (bbox-of-cells cells)))
        (length
          (positions-in-rect
            (first bb) (second bb) (third bb) (fourth bb)))))
    (let* ((colors (grid-colors g 0))
           (selector-color
             (first
               (filter
                 (lambda (color)
                   (= (length (find-color g color)) 3))
                 colors)))
           (selector-area
             (bbox-area (find-color g selector-color))))
      (for/fold ([out (empty-grid (rows g) (cols g) 0)])
                ([color (in-list colors)])
        (let ((cells (find-color g color)))
          (if (and (= (length cells) 4)
                   (>= (bbox-area cells) selector-area))
              (let ((bb (bbox-of-cells cells)))
                (paint-cells
                  out
                  (positions-in-rect
                    (first bb) (second bb) (third bb) (fourth bb))
                  color))
              out))))))