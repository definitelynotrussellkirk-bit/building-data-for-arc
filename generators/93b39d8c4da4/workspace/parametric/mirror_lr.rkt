(rule!
  (let ((dummy 0))
    (define shape (normalize-cells (find-color g 2)))
    (define transformed (normalize-cells (flip-cells-lr shape)))
    (define stamps
      (flatmap
        (lambda (mark)
          (map
            (lambda (p)
              (list (+ (first mark) (first p))
                    (+ (second mark) (second p))))
            transformed))
        (find-color g 3)))
    (paint-cells (empty-grid (rows g) (cols g) 0) stamps 8)))
