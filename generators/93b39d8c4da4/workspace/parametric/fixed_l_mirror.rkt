(rule!
  (let ((dummy 0))
    (define shape
      (normalize-cells
        (flip-cells-lr
          (list (list 0 0) (list 1 0) (list 2 0) (list 2 1)))))
    (define stamps
      (flatmap
        (lambda (mark)
          (map
            (lambda (p)
              (list (+ (first mark) (first p))
                    (+ (second mark) (second p))))
            shape))
        (find-color g 3)))
    (paint-cells (empty-grid (rows g) (cols g) 0) stamps 8)))
